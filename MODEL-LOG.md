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

## 1.51 Audit: every "it has no effect" this project has acted on (2026-08-19)

Prompted by the project owner asking whether the near-zero width rows meant the
mechanisms were broken, and then the sharper follow-up: **have we removed things
on a no-effect measurement that was itself wrong?** There is precedent —
`poll_k` was certified inert on a null measured with its gate shut, and had to
be retracted — so the question was worth answering properly rather than
reassuringly.

### What was removed, and what the removal rested on

| removed | evidence it rested on | is that evidence sound? |
|---|---|---|
| `polling_lean`, `polling_span` | **static**: computed, passed to `pool_spec`, and the body never references the parameter | yes — not a measurement at all, so no measurement to be wrong |
| `pool_spec(base_city_d)` | same, an unread argument | yes |
| `first_local_election` | measured **worse** than the spine: 36/46 paired, p = 0.00016, and it carries strictly less information (sd(log) 1.19 vs 0.74) | yes — a "worse" claim, not a "no effect" claim, and the two have different failure modes |
| `turnout_tilt_da` | removed as **broken**: applied after `solve_and_predict` had calibrated, so rows stopped summing to one | yes |
| `pa_contestation_uplift` | removed as a one-party rule, not for inertness — and generalising it exposed a double count (§1.47) | yes, and productive |
| **`ward_pr_ratio_overrides`** | **consumption**: `run.constants_read` says read at no target, because it is gated on `not fallback` and the fallback is always present | **this is the gate-shut pattern**, and it is the one to check |

### The gate-shut ones, re-checked today at every runnable target

`ward_pr_ratio_overrides` and the `theta_mode` / `f_other` pair were both retired
on "consumed at no target", which is exactly the shape of reasoning that made
`poll_k`'s null wrong. Re-measured across all ten runnable city-years:

* **`ward_pr_ratios` returns a fallback at every one of them**, so the override
  could never have fired. The deletion holds.
* **The spine misses zero parties at every one of them**, so `theta_prior`'s
  fallback branch — the only consumer of `theta_mode` and `f_other` — is
  unreachable. Those entries hold.

The residual risk is stated rather than dismissed: both are inert **because a
gate is shut at every target the harness can run**, not by construction. A city
or target with no preceding LGE file would open the first gate, and the override
is gone. The code's own comment says the fallback replaces it by design, so that
is a deliberate position — but it is a position, not an arithmetic fact.

### The false-negative channel that was real

§1.37 records it: **CLASS 12 compared list shares only**, and on that evidence
called `ward_noise_sd` and `pa_contestation_uplift` dead. Both are live on the
ward side. The sweep now compares list ballot, ward ballot, ward wins **and**
seats, which is why the same class of error surfaced immediately this week when
the width budget's citywide-only view called the turnout knobs zero.

**That is the general lesson, and it has now bitten twice: a null is only as
broad as the output it was measured on.**

### What continuous enforcement exists

`test_every_tunable_lever_actually_moves_the_forecast` fails in **both**
directions — a lever that should move and does not, and **a lever that moves
while `EXPECTED_INERT` claims it does not**. So every inertness claim in this
repository is re-checked on every suite run rather than standing on the day it
was written. `overhang_rule` retired its own excuse that way, one day after it
was written (§1.47).

Two gaps that enforcement does not close, recorded so they are not mistaken for
covered:

* it runs at **40 draws** and two targets, so a lever that fires rarely can read
  inert — which is precisely what happened to `overhang_rule`, whose clause fires
  in 1 draw of 200;
* **`entrant_geography`'s mechanism is untested.** The entry is honest that the
  perturbation supplies no `parent` and therefore tests only that the EMPTY
  default is inert. Nothing has ever exercised the mechanism itself.

### And the one this audit started from

The register says `turnout_noise_sd` contributes "~0.003 citywide, **i.e.
nothing**". Checked on the scored metrics rather than on citywide share: across
jitter 0 → 0.60 and noise 0 → 0.30, coherent seat error and ward MAE are
unchanged and CRPS moves by **0.016%** (91.6695 → 91.6839 over two city-years).
So "nothing" is defensible for scoring. It moves 46 ward wins, which is real and
was not in the record; it does not propagate, because coherent seats apportions
the **mean** seat vector and per-draw flips average out.

---

## 1.52 The party-specific constants are gone, two days after they should have been (2026-08-19)

The project owner, seeing `pa_contestation_uplift` in the §1.51 audit table:
*"Twice we have removed all party-specific rules like this. How can it still be
in the code, let alone live?"*

### What was actually still there

`pa_contestation_uplift` was **not** in the code — deleted 2026-08-18 (§1.47),
and the sightings were historical comments plus a frozen HTML artefact. But the
question was the right one to ask, because a scan of the forecast path for
hard-coded party names found **twelve party-specific numbers still sitting in
`DEFAULTS`**:

* `theta_mode` — ANC 0.75, EFF 0.85, MK 0.60, DA 1.30, ASA 1.50, BOSA 0.80
* `individual_theta` — PA, Al Jama-ah, IFP, VF+, ACDP, RISE, each a
  (low, mode, high) band
* `f_other` — the residual bucket those two fell through to

All three were **certified dead at every runnable target** and carried anyway:
in `DEFAULTS`, in `apply_city`, in two city tomls, in `EXPECTED_INERT` and in
the register. Their disposition was written up in §1.41 as *"an open decision"*.

**It was not open.** The owner had already given it, twice, and it is on the
record: *"If something is dead and no longer used, why would we want to keep it
around — unless it should not be dead."* Keeping them was not caution, it was a
failure to act on an instruction, and it is the third time this project has
found a deleted-or-dead lever still sitting in a place someone reads.

### Deleted, and it moves nothing

Both dead precedence branches in `blended_centres`, the dead-store write of
seeded arrivals' bands into `individual_theta`, the `apply_city` copy, the two
city tomls, the register rows and the `EXPECTED_INERT` entries. The
`f_other` branch is replaced by an **explicit `raise`**: a party with a national
baseline, no spine level, no θ prior and no seed is a combination the branches
above make impossible, and if it ever happens it should be loud rather than
absorbed by a typed number for whichever parties someone named in 2026.

Johannesburg, Tshwane and Cape Town 2021 at 400 draws are **identical to every
digit** before and after — 86/65.470, 30/25.970, 32/30.656. They were dead, as
certified.

### What party-specific material remains, and why

The same scan is the way to check this claim rather than trust it. What is left
in the forecast path:

| what | verdict |
|---|---|
| `PLAN_BOUNDS` — per-party θ sanity ranges | **live**, read in the by-election clamp for a party with no θ prior. Already 🔴, and already recorded as a diagnostic the model prints against itself and ignores. Not touched here |
| `pools.Split(...)` — COPE from ANC, EFF from ANC, NFP from IFP, GOOD from DA, MK from ANC, ASA from DA | **historical fact**, not a rule: who actually split from whom. Party-specific because the world is |
| `WITHOUT = ("ANC", "EFF", "MK")` | a **reported statistic** — "can a majority form without these three" — not a modelling rule, and the code says so |
| `gate_parties = ["ANC", "DA", "EFF"]` | the dimension-admission test set, methodology rather than forecast |
| `indicator = "IFP"` | simulation-only bloc, not the published spec |

### And deleting them exposed a golden test that was guarding nothing

`tests/test_drawer.py`'s fixture loaded the pool spec and stopped. It never ran
the spine and never built a θ prior, so every party reached `blended_centres`
with neither, fell through the precedence chain, and took its centre from
`theta_mode`, `individual_theta` or `f_other`. Deleting those three is what
exposed it — the golden prior turned out to be **anchored on the dead
constants, and on nothing the forecast uses.**

It also explains a silence that had been read as evidence. When §1.49 changed
what `theta_prior` shrinks toward, these values did not move, and that was taken
as confirming the change was inert. It confirmed nothing: **the fixture was not
calling `theta_prior` at all.**

The fixture now builds the level the way `run_model` does, and the prior moves a
long way — ANC 21.71 → 21.28 on a much tighter band (6.59–40.46 → 10.19–34.53),
DA 27.95 → 24.51, ASA 12.48 → 14.12, MK 7.25 → 10.12. That is a **different code
path, not a changed model**: the spine's levels are better informed than a
residual bucket of 1.30, so the bands narrow. Re-recorded with the reason in the
file.

**The nine city-years are unaffected and were not re-run for it.** They go
through `run_model`, which has always built the level this way. What changed is
only what the golden test characterises — which is now the thing that ships.

### The frozen artefact, which is what was actually seen

`forecast-interactive.html` and `site/dev/interactive.html` are **tracked** and
still carry a "PA's wider slate" slider, because they were built on 7–8 August
and `build_interactive.py` now **refuses to rebuild them**: the interactive was
never ported to voter pools, its in-browser drawer is the old two-bloc engine,
and the page is deliberately frozen.

So a reader opening either file sees a control for a constant the model deleted,
driving an engine the model replaced. That is not a stale figure, it is a stale
*program*, and it is the same shape as `site/plan.html` being served for weeks
after no build produced it. **Nothing in the model reads them**, but they are
tracked, and a tracked file that looks current is exactly the trap this
repository keeps setting for itself. Flagged rather than fixed, because deleting
or re-banner-ing a published artefact is the owner's call.

---

## 1.53 `entrant_geography` was never dead — the perturbation was the identity (2026-08-20)

§1.51's audit named this as the one inertness claim whose *mechanism* had never
been exercised. Exercised now, and it is live at both targets.

### The mechanism

`dev[:, ENTRANT] = (1 − k) · dev[:, parent]` — the generic arrival slot inherits
a named parent's per-voting-district map, scaled. It is off by default because
`entrant_geography` is `{}` and the branch needs a `parent`.

Supplying one, Johannesburg, 200 draws, hashing PR shares, ward shares and seat
draws together:

| | result |
|---|---|
| default `{}` (no parent) | baseline |
| `parent ANC, k = 0.0` | **moves** |
| `parent ANC, k = 1.0` | **byte-identical** |
| `parent DA, k = 0.0` | moves, and differently from ANC |

The `k = 1.0` row is the useful one: it is flat *by construction*, so a
perturbation that moves at k=0 and not at k=1 is demonstrably reaching the code
rather than merely differing from it.

### Two wrong explanations of one non-perturbation

`PERTURB` carried `{"parent": "ANC", "k": 1.0}` — **the identity**. So the sweep
had been perturbing this lever to a value that cannot change anything, which is
`ITERATING.md` rule 6's fault outright.

And the `EXPECTED_INERT` entry that excused the resulting null gave the wrong
reason for it. It said *"the branch needs a declared `parent`; the perturbation
used here supplies none"*. A parent **was** supplied. The null came from the k,
not from the parent — so the entry was honest in tone, precise in wording, and
wrong on the fact. It read as a careful disclosure, which is exactly why it
survived §1.51's audit with only a note that the mechanism was untested.

Fixed to `k = 0.0`, and the `EXPECTED_INERT` entries are deleted: the lever is
live at 2021 and 2026 and belongs in the ordinary sweep.

### What this does not change

Nothing in any forecast. `entrant_geography` remains `{}` by default and no
committed run supplies a parent, so this is a test that now tests something and
a register that now says something true. The mechanism itself is still
**argued, not tested** in the sense that matters — no backtest has ever scored
an arrival against an inherited map versus a flat one, and the k values quoted
in the code (0.03 for MK on the ANC, 0.05 for the EFF on the ANC, 1.00 for
ActionSA on the DA) come from a fit that predates this sweep.

---

## 1.54 The tail's over-forecast is not worth fixing, and the obvious fix makes it worse (2026-08-20)

§1.44 shipped the level shrink with a cost recorded openly: the freed mass is
returned by uniform renormalisation, which is a multiplicative boost with many
micro-parties to collect it, so **ranks 13+ went from very nearly unbiased to
over-forecast**. Three targeted redistributions were measured then and all
scored worse — but each had re-fitted its own `c`, so the comparison was
confounded, and the question was left open.

Reopened properly. A **soft receiver floor** was built as a lever: a party's
share of the freed mass weighted by `q/(q + floor)`, which is ~1 above about a
percent and falls smoothly to zero for a micro-party. Soft rather than a cut-off
so nothing turns on where a line falls. Four metros at 2021, 600 draws, `c` and
`h` held at their committed values so only the destination varies:

| `level_shrink_floor` | coherent seats | CRPS | ranks 1-3 | ranks 4-12 | ranks 13+ |
|---|---|---|---|---|---|
| **0.0 — uniform, shipped** | **168** | **147.4** | +12.94 | **−17.79** | +1.52 |
| 0.001 | 182 | 153.6 | +15.53 | −18.26 | −0.53 |
| 0.002 | 182 | 154.1 | +16.00 | −18.41 | −0.95 |
| 0.005 | 190 | 157.8 | +17.93 | −19.65 | −1.33 |

**It closes the tail and costs 14 to 22 seats to do it.**

### The hypothesis that motivated it is refuted

The reason to try was arithmetic: the tail is over by some amount and ranks 4-12
are under by more, so mass withheld from the tail might land in the middle. **It
does not.** Ranks 4-12 get *worse* at every floor, and ranks 1-3 worse still —
+12.94 to +17.93. The receiver weight `q²/(q+floor)` favours large `q` by
construction, so withholding from the tail sends the mass **to the top of the
ballot**, which is the band already over-forecast. The fix feeds the fault it
was meant to relieve.

### And the tail is small

From the committed artefact, seats at stake across nine city-years: ranks 1-3
**1,464**, ranks 4-12 **257**, ranks 13+ **31**. The tail is **1.8%** of what is
being contested. Its +5.60pp signed error is a real bias on a band that decides
almost nothing.

### Disposition

**Not fixed, and the lever is deleted** rather than left in `DEFAULTS` at an
inert default — the same treatment `first_local_election` got, for the same
reason: a mechanism measured worse is a negative result, not an option. Uniform
renormalisation stays, and it is now the *measured* choice rather than the
unexamined one.

What would still be worth trying, and is not this: a redistribution whose
weights favour the **middle** rather than the top — the band that is actually
short. Every form tried so far is monotone in size, which cannot do that. That
needs the joint width calibration's machinery (task #10) rather than another
one-parameter reweighting.

---

## 1.55 The dominant width lever is sweepable at last, and a scalar cannot serve both bands (2026-08-20)

> **PARTLY SUPERSEDED BY §1.56 the same day — read that first.** The ranks 4-12
> `sd(z)` column below was measured on the `claimed` population, whose
> membership moves with the lever (30 / 37 / 45 columns across the three
> settings) and which excludes the model's worst columns by construction. On a
> fixed population ranks 4-12 read 1.553 / 1.940 / 2.267, so **"ranks 4-12 want
> 2.0" is backwards.** The ranks 1-3 column, the lever itself, and the decision
> to ship at 1.0 are unaffected. Left in place unrewritten because the mistake
> is the finding.

§1.48 found the within-pool Dirichlet supplying **83–98% of drawn variance for
every party except the ANC and DA** — the model's dominant width lever — and
noted that it sat in the register as a *concentration guard* and had never been
swept against realised width. It had no handle at all: `alpha` is fitted per
pool by method of moments and baked into the emitted spec.

`dirichlet_scale` is that handle. It multiplies every pool's fitted
concentration, so above 1.0 narrows the forecast and below 1.0 widens it, and
1.0 is exactly the fit. It multiplies rather than replaces because the per-pool
fit carries real information about which pools are volatile, and a single
replacement value would throw that away to move one number.

### Nine city-years, 600 draws

| `dirichlet_scale` | coherent seats | CRPS | beats u-swing | ranks 1-3 sd(z) | ranks 4-12 sd(z) |
|---|---|---|---|---|---|
| 0.5 — wider | 274 | 256.0 | 7/9 | 0.694 | 0.698 |
| **1.0 — the fit** | **258** | 231.9 | 7/9 | 0.844 | 0.856 |
| 2.0 — narrower | 260 | **222.1** | 7/9 | 1.191 | **0.974** |

**The lever works, and it works on everything.** It moves seat error, CRPS and
both bands' width together, which is what a dominant variance source should do
and is the confirmation §1.48's ablation was reading something real.

### And it demonstrates the problem it was built to solve

**Ranks 4-12 want 2.0** — `sd(z)` 0.974 against a nominal 1.0, very nearly
correct, from 0.856. **Ranks 1-3 want about 1.0** — at 2.0 they go from too wide
(0.844) to too narrow (1.191), roughly equally wrong in the other direction. One
scalar cannot serve both, which is the same shape as `SD_FLOOR`'s trade in §1.50
and the reason task #10 exists.

### Not adopted, and the reason is rule 10 rather than the score

CRPS clearly prefers 2.0 (231.9 → 222.1) and the seat difference is 258 → 260,
inside the ±2–4 draw noise. On the scoreboard alone 2.0 is arguably the better
setting.

**Nothing outside the scoreboard picks it.** The fitted 1.0 comes from a method
of moments estimate of historical within-pool concentration — that is the
external evidence, and it names 1.0. Adopting 2.0 would be choosing a constant
because it scores well on these nine city-years, which is exactly what
`ITERATING.md` rule 10 refuses and what `entrant_prob = 0.40` and
`spine_k = 0.25` were already refused for.

So `dirichlet_scale` ships at **1.0**, as an instrument rather than a tuning: the
biggest lever in the model now has a handle, a sweep and a register row, and the
next attempt on width has something to pull.

### What the successor has to be

Not a better scalar. The bands want different concentrations, so the target is a
**size- or band-dependent** concentration — or a per-pool one fitted against
realised width rather than against historical within-pool variance. That is a
genuine joint calibration, it needs `src/width_budget.py` as its instrument, and
it must be validated the way the level shrink was: fit on one cycle, apply to
the other, never chosen on the nine.

---

## 1.56 The calibration denominator moved with the lever, and it moved away from the failures (2026-08-20)

An independent pollster review flagged this and it is a real defect in the
measuring instrument, not in the model. It has been confirmed, and following it
through says something sharper — and more useful — than the review found.

### The defect

`score.CLAIM_FRACTION` selects the scored `claimed` population as "a seat in at
least half this forecaster's draws". `score.score_seats`' docstring defends that
at length and is **right**: selection on the forecast is neutral, PIT uniformity
survives it, and a forecaster is answerable for its own claims. That argument is
about ONE forecaster. A lever sweep is a comparison ACROSS forecasters, and
there the criterion admits a different set of columns to each of them.

Measured, nine city-years, 1500 draws:

| `dirichlet_scale` | `claimed` columns | of which ranks 4-12 | `reference` columns | with defined `z` |
|---|---|---|---|---|
| 0.5 — wider | 58 | 30 | 252 | 225 |
| **1.0 — committed** | 67 | 37 | 252 | 225 |
| 2.0 — narrower | 81 | 45 | 252 | 225 |

**Narrowing admits columns**, which is the direction that surprises. A tighter
draw puts a party whose mean is above the threshold into nearly every draw
instead of into some of them; widening scatters draws back onto zero and the
party drops out of its own scored population. The criterion rewards confidence
with a larger denominator.

### The fix

`compare_history.reference_universe` — a fourth population selected from inputs
alone. A party is in if it took at least `REFERENCE_SHARE = 0.25%` of the
combined ward+PR vote at the **previous** local election, or stands in at least
`REFERENCE_SLATE = 25%` of this election's wards. Both are known before polling
day; neither can move when a lever moves. It is scored through
`score.seat_matrix(..., keep_all=True, parties=...)`, because a mask over the
ordinary matrix is not enough — that matrix drops a column that is zero on both
sides, so the forecast-dependence walks straight back in through the universe
after being shut out of the mask.

Both constants are **declared, not measured**, and are in `JUDGEMENT-CALLS.md`.
The slate cut is the weaker one: on a strict reading a party can win a ward seat
with one ward, so the principled threshold is "on the ballot", which admits 24
to 57 parties a city-year and reproduces the dilution that makes `all`
untestable. Sensitivity over the panel: **252 columns at 0.25, 232 at 0.50, 211
at 0.75.**

### What it says, and it is not what §1.55 said

`sd(z)`, nine city-years, 1500 draws. `IQR-sd` is the interquartile range over
1.349 — the same statistic robust to a handful of columns:

| scale | band | `claimed` n | `claimed` sd(z) | `reference` n | `reference` sd(z) | `reference` IQR-sd | `reference` \|z\|>3 |
|---|---|---|---|---|---|---|---|
| 0.5 | 1-3 | 27 | 0.662 | 27 | 0.662 | 0.303 | 0 |
| 0.5 | 4-12 | 30 | 0.612 | 74 | **1.553** | 0.395 | 3 |
| **1.0** | 1-3 | 27 | 0.855 | 27 | 0.855 | 0.421 | 1 |
| **1.0** | 4-12 | 37 | 0.823 | 74 | **1.940** | 0.595 | 4 |
| 2.0 | 1-3 | 27 | 1.178 | 27 | 1.178 | 0.480 | 1 |
| 2.0 | 4-12 | 45 | 0.916 | 74 | **2.267** | 0.715 | 9 |

`n` above is the count of columns with a **defined `z`** — a column whose draws
are all identical has no scale and stores `None`. The fixed population is 252
columns of which 225 carry a `z` (27 at ranks 1-3, 74 at 4-12, 124 at 13+), and
those three counts do not move across the sweep either. The pooled PIT tables
count PIT values instead and their `n` is larger (76 and 139); `pooled_by_band`
now stores `n_z` so a width figure can be labelled with the columns it was
actually computed on.

~~**Ranks 13+ read `sd(z)` 0.364 with mean z −0.125** on the fixed population —
intervals about 2.7× too wide on a band that is also over-forecast (+5.60pp,
§1.54).~~ **WRONG, corrected the same day in §1.58.** `sd(z)` is not a width
statistic on a near-degenerate discrete column: where the forecast is
approximately Bernoulli(p) and the truth is zero, `z = −√(p/(1−p))` exactly —
a deterministic function of the forecast probability with no room to spread.
Verified on the 96 ranks-13+ columns where the truth is zero: observed `z`
correlates with `−√(p/(1−p))` at **+0.93**. So `sd(z)` on that band measures the
spread of *p* across micro-parties, not calibration. On the discreteness-safe
statistic ranks 13+ read **probit-SD 1.188** — slightly too NARROW, not 2.7×
too wide. §1.58.

**Ranks 1-3 are identical in both populations at every setting** — the same 27
columns, because the top three parties are always claimed. §1.55's reading of
ranks 1-3 stands untouched, and so does its conclusion that they want about 1.0.

**Ranks 4-12 reverse.** `claimed` says 0.823 — too wide, narrow it, and 2.0 gets
it to 0.974. `reference` says **1.940 — about half as wide as it should be**, and
narrowing to 2.0 makes it 2.267, further from 1.0 rather than closer. §1.55's
"ranks 4-12 want 2.0" is therefore not merely unsupported: it is **backwards**,
and the half of "a scalar cannot serve both bands" that rested on it is
withdrawn.

### The sharper statement: the rule selects away from the failures

Two columns carry the whole difference — **Cape Town's Cape Coloured Congress at
z = +12.1 and Johannesburg's PA at +9.3** — and both are outside `claimed` and
inside `reference`. That is not a coincidence and it is worse than a moving
denominator:

> A party the forecaster gives a seat in fewer than half its draws is exactly a
> party the forecaster is failing on. `CLAIM_FRACTION` excludes it from the
> population that exists to test the forecaster.

The model's six zero-probability columns (§1.54, and the review's list) are
precisely the columns `claimed` cannot see. The instrument was blind in the one
direction the model is worst.

### And the real width story is bulk against tail, not band against band

On `reference` ranks 4-12 at the committed setting: `sd(z)` 1.940, `IQR-sd`
0.595. The bulk of the band is **too wide by about 40%** and the tail is
catastrophically thin, with four columns beyond \|z\|>3 rising to nine at scale
2.0. Those are the same two numbers pointing opposite ways, which is why no
scalar has ever satisfied both and why every scalar sweep has produced a trade
rather than an optimum.

So the successor §1.55 asked for is still a mixture, but for a **different
reason than §1.55 gave**: not because two rank bands want different
concentrations, but because the bulk and the tail of one band do. That is task
A2, and this population is the instrument it is measured on.

### Why this differs from the review's own numbers

The review reached the fixed-set question by **intersecting** the `claimed` sets
across settings — 56 common columns — and read ranks 4-12 at 0.964 and 1.189.
An intersection of forecast-selected sets is still forecast-selected: every
column in it was claimed by every forecaster in the sweep, so the failures are
excluded from the intersection by exactly the rule that excluded them from each
set. The review's diagnosis of the defect is right and its correction is not
strong enough. Its recommended `dirichlet_scale = 1.4` is **not adopted**, and
its own second item is why: at 1.4 the seats won by parties outside every draw
go 19 → 55.

### Disposition

- Reported in `history.md` as a fourth population, printed first and labelled as
  the only one to compare on. `claimed` stays and stays the answer to "is this
  model calibrated"; `reference` is the answer to "did that change help".
- **Coverage and PIT on `reference` read optimistically by construction** and
  are not calibration figures in absolute terms — a fixed population must carry
  columns that are zero on both sides, and each is a free interval hit. The
  dilution is identical at every setting, which is what makes differences
  readable. `sd(z)` is largely immune: a column with no draw variance stores
  `None` and leaves the width figure without being selected out of the
  population.
- Two tests, `tests/test_calibration_report.py`: one asserts the `claimed`
  denominator moves between two forecasters differing only in width, one asserts
  `reference` scores the universe it is handed and keeps the column the
  forecaster fails worst on.
- **The change is inert on every existing number.** The committed setting
  reproduces 254 coherent / CRPS 232.9 exactly.

---

## 1.57 Uniform swing is not a strawman — the optimal blend IS uniform swing (2026-08-20)

**Negative result.** The pollster review's item A6 objected, correctly, that
`last-lge` (594 coherent seats) and `prior-lge-noise` (561) are not references,
and that quoting a 3.4× margin over them invites the charge that the baselines
were chosen to be beaten. The professional answer is Murphy's convex combination
of the two naive forecasts. It was built and measured, and it does not exist.

### The family collapses to one parameter

    w · (prev + swing) + (1 − w) · prev  ==  prev + w · swing

The convex combination of uniform swing and persistence is **a damped swing**.
`w = 1` is `uniform-swing`, `w = 0` is `last-lge`, and the whole family is the
classic swing-damping correction. `benchmarks.blended_swing`, `BLEND_W`.

### The optimum is on the boundary

Coherent-comparable seat error, nine city-years, deterministic:

| `w` | 0.0 | 0.25 | 0.50 | 0.75 | 0.90 | 0.95 | **1.00** | 1.05 | 1.15 | 1.30 |
|---|---|---|---|---|---|---|---|---|---|---|
| seat error | 594 | 524 | 456 | 404 | 382 | 376 | **376** | 372 | 372 | 382 |

Monotone decreasing across the entire interval. **No damping helps at all**, and
the best convex blend is uniform swing itself.

The unconstrained grid optimum is `w = 1.05` at 372 — which is not a blend but an
*amplified* swing, is worth 4 seats in 376, and sits on a plateau (376 / 376 /
372 / 374 / 372 / 374 / 376 from 0.95 to 1.25). **It does not survive
leave-one-out.** Seven of nine folds choose 1.05 and two choose 1.15, and the
held-out errors total **380 against uniform swing's 376**. A fitted baseline that
loses to the unfitted one out of sample is not a baseline.

### Disposition

- `blended-swing` stays in `BENCHMARKS` so the check is repeatable, with
  `BLEND_W = 1.0`. It is **not** printed as a fourth column: a column identical
  to `uniform-swing` is noise in a table.
- `ITERATING.md` records this so it is never re-litigated, which was the review's
  own stated abandon-condition.
- What it establishes is worth having: **uniform swing is the strongest member of
  the naive family on this panel**, so the margin quoted over it — 254 against
  376 — is honest, and the two weak baselines are context rather than the claim.
- It does **not** answer the harder objection, which stands and is now disclosed
  separately (§A7, `history.md`): the margin is a Gauteng result. Inside Gauteng
  the model takes **42%** off uniform swing's seat error; outside it, **10%**,
  and it loses at Mangaung.

---

## 1.58 The width question, answered per band on a fixed population — and two of this project's three width statistics are invalid where it used them (2026-08-20)

§1.56 fixed the population. This fixes the statistic, and the two together give
the first reading of this model's width that is not confounded by something.
**It also corrects §1.56's own ranks 13+ paragraph, written four hours earlier.**

### First: "outside every draw" is not a property of the forecast

The review's item A2 gates on *seats won by parties the truth exceeded in every
draw*, and reports 19 seats rising to 55 under `dirichlet_scale = 1.4`. That
statistic depends on the DRAW COUNT as much as on the model. At 600 draws six
columns carry PIT 1.0; **at 1500 draws it is four columns and four seats**,
because the PA at Johannesburg 2021 and the Cape Coloured Congress at Cape Town
fall inside the sample once there are enough draws to reach their tail. Nothing
about the model changed.

Re-measured at 1500 draws it does not discriminate at all:

| `dirichlet_scale` | 1.0 | 1.4 | 2.0 |
|---|---|---|---|
| seats won at `P(≥1 seat) < 0.02` | 4 | 4 | 4 |
| seats won at `P(≥1 seat) < 0.10` | 4 | 4 | 4 |

So `calibration_columns` now stores **`p_any`** — the fraction of draws giving
each column at least one seat — and any gate is written on that. It is also
exactly the quantity the publication gate asks for (`PUBLISHING-BACKLOG.md` §5b
item 1).

**And the two headline failures are not zero-probability at all.** At the
committed setting the Cape Coloured Congress has `P(≥1 seat) = 0.118` and won
seven; the PA at Johannesburg has **0.307** and won eight. The model does not
say they are impossible. It says they are small, and they were not. That is an
error of SIZE, and it is a different repair from an error of possibility.

### Second: `z` is not a width statistic on a near-degenerate column

Where a seat column is approximately Bernoulli(p) and the truth is zero,

    z = (0 − p) / √(p(1−p)) = −√(p / (1−p))

exactly — a deterministic function of the forecast probability, with no room to
spread whatever the intervals are doing. Checked rather than asserted: on the 96
ranks-13+ columns where the truth is zero, observed `z` correlates with
`−√(p/(1−p))` at **+0.93**.

So `sd(z)` on ranks 13+ measures the spread of *p* across micro-parties.
§1.56's *"ranks 13+ read sd(z) 0.364 — intervals about 2.7× too wide"* is
withdrawn; the entry is annotated in place.

The three statistics have complementary failure modes and the project has now
been caught by each:

| statistic | exact when | fails when | caught |
|---|---|---|---|
| coverage at one level | never alone | confounded with the level | ITERATING rule 8, twice |
| probit-SD | discrete columns fine — randomised PIT is uniform under calibration whatever the support | **attenuated by a level shift** | §1.36 |
| `sd(z)` | continuous columns, exact under a shift | **meaningless on a low-`p` discrete column** | here |

### The reading, per band, on the fixed population with the statistic valid there

`dirichlet_scale` swept to 16× — far past anything contemplated — to find the
ceiling. probit-SD, 1.00 correct, below 1.00 too wide:

| scale | coherent | CRPS | ranks 1-3 | ranks 4-12 | ranks 13+ |
|---|---|---|---|---|---|
| 0.5 | 262 | 256.4 | 0.549 | 0.936 | 1.208 |
| **1.0** | **254** | **232.9** | **0.682** | **1.020** | **1.188** |
| 1.4 | 258 | 226.5 | 0.775 | 1.111 | 1.184 |
| 2.0 | 262 | 221.6 | 1.077 | 1.227 | 1.179 |
| 4.0 | 260 | 217.1 | 1.121 | 1.288 | 1.180 |
| 8.0 | 262 | 213.9 | 1.161 | 1.529 | 1.186 |
| 16.0 | 258 | 212.5 | 1.180 | 1.670 | 1.192 |

Three separate findings, and none of them is the one this project has been
working from.

**1. Ranks 1-3 are the band that is too wide, by about 1.5×** (probit-SD 0.682).
Its mean `z` is −0.009, so there is no shift to attenuate the statistic and it
can be read at face value. It is also the band that RESPONDS: 0.682 → 1.077 by
scale 2.0.

**2. Ranks 4-12 cannot be described by one width, and that is the finding.**
Three valid-looking statistics on the same 74 columns disagree: `sd(z)` 1.940
(far too narrow), `IQR-sd` 0.595 (too wide), probit-SD 1.020 (about right, and
attenuated by a mean `z` of +0.796, so the true value is higher). They disagree
because the error distribution is a narrow shifted bulk with two enormous
outliers — the CCC at `z` +12.1 and the PA at +9.3. **A distribution that reads
"too wide", "about right" and "far too narrow" depending on which moment you
take is not mis-scaled, it is mis-SHAPED**, and no scalar can fix it. That is
the real case for A2's mixture, and it is a different case from the one the
review made.

**3. Ranks 13+ do not move at all, and `dirichlet_scale` is not their lever.**
probit-SD goes 1.208 → 1.192 across a **32-fold** change in concentration. 124
of the 225 fixed columns sit in that band. Whatever sets their width, it is not
the within-pool Dirichlet — the candidates are the θ level shock and `SD_FLOOR`,
which is task A5's territory. Recorded as a hypothesis, not a finding.

### And the lever cannot reach correct width anywhere

At 16× concentration — 32× the low end — overall `IQR-sd` is 0.766 and ranks 1-3
probit-SD is 1.180, having crossed 1.00 somewhere near scale 2.0. Meanwhile the
tail gets steadily worse: max `z` 12.1 → 19.2 and columns beyond \|z\|>3 going
5 → 14. **CRPS improves monotonically the whole way (232.9 → 212.5) while
coherent seats stay flat at 254–262**, which is worth stating plainly: CRPS
wants the forecast narrower than the seat error does, all the way out, and a
width decision taken on CRPS alone would run to the end of the sweep.

### Disposition

- Nothing retuned. `dirichlet_scale` stays at **1.0**, the method-of-moments
  fit, for the reason §1.55 gave and this does not disturb.
- `p_any` is stored, and gates are written on it rather than on "outside every
  draw".
- **A2's brief changes.** Not "narrow the bulk and add a realignment component
  because the tail is thin" — the tail is not thin in the way the review
  measured, and the band whose bulk is too wide is ranks 1-3, not 4-12. The
  object is a component structure that lets ranks 1-3 narrow while ranks 4-12
  keeps its heavy right tail, with `π` still estimated from the archive.
- **A5 is promoted.** 124 of 225 columns are inert to the model's dominant width
  lever, and the width question for them has never been asked of the right
  constant.

---

## 1.59 `SD_FLOOR` is right, and the rest of the θ prior is 1.7 to 3.5× too narrow (2026-08-20)

§1.50 argued that `SD_FLOOR = 0.15` is "approximately the CONDITIONAL dispersion
this layer should carry", and the review's item A5 objected — correctly — that
**nothing in the repository computes the conditional dispersion**, so the
constant sat at 🟡 on the strength of a sentence and two errors that happened to
cancel. `src/theta_residual.py` computes it.

### What is measured

For every target LGE and every metro, from strictly earlier cycles only:

    residual = log(observed θ) − log(the centre `theta_prior` gave that party)

Both the centre and the width come from `levels.theta_prior` itself, called with
the real baseline for that metro-year — the preceding national election's
citywide shares, which is what `montecarlo` passes it. Intervals are cluster
bootstrapped on metro-year, because every party in one metro-year shares that
year's shock and an ANC collapse is not eight independent facts.

| national size | n | metro-years | measured | 95% CI (cluster) | width the model uses | ratio |
|---|---|---|---|---|---|---|
| < 0.2% | 78 | 17 | 0.915 | [0.683, 1.065] | 0.460 | **1.99×** |
| 0.2 – 1% | 96 | 18 | 0.737 | [0.565, 0.869] | 0.340 | **2.17×** |
| 1 – 5% | 32 | 16 | 0.448 | [0.274, 0.613] | 0.263 | **1.70×** |
| 5 – 15% | 14 | 13 | 0.663 | [0.243, 1.008] | 0.188 | **3.53×** |
| **≥ 15%** | 37 | 18 | **0.138** | **[0.084, 0.171]** | **0.150** | 0.92× |

### First finding: §1.50 was right, and it is now measured rather than argued

At the top of the ballot the conditional dispersion is **0.138** and the model
uses **0.150** — inside the interval. The MARGINAL record for the same parties
is 0.222 and the chi-square-corrected fit would be 0.260; both are far outside
it. So §1.50's reasoning holds: the layer is conditional, the record is
marginal, and applying `LOG_CHI2_BIAS` would count the within-pool Dirichlet's
variance twice. That is why the correction scored worse on everything (§1.50),
and now there is a number saying why rather than an argument.

`SD_FLOOR` is what puts the width there — it binds on **20 of the 37**
observations at or above 15%, and never below 5% of the vote. It is a
top-of-ballot constant that lands on the measurement. Better defended than it
was; still not derived. **🟡 → 🟢 on the top bin only.**

Note also what this says about §1.50's confounded test, which the review flagged:
the objection was that applying the correction ALSO stopped the floor binding,
so two things moved at once. It does not matter to the conclusion. The corrected
width at the top of the ballot would be 0.260 and the measured quantity is 0.138
with an upper bound of 0.171 — the correction is refuted on its own, without
needing the arm to be clean.

### Second finding, and it is the larger one: everywhere else is far too narrow

**In all four bins below 15% the cluster-bootstrap interval excludes the width
the model uses**, always in the same direction. The best-supported bins (n=96
and n=78) exclude it comfortably; the largest ratio (5–15%, 3.53×) has the
fewest observations and the widest interval and should be read as the weakest of
the four, not the headline.

The cause is visible in the estimator. `sd_for` is a straight line in log(size),
and the measured conditional dispersion is **not monotone** in size — 0.915,
0.737, 0.448, 0.663, 0.138. A line cannot be right in the middle and at both
ends, and this one is anchored at the ends.

**This converges with §1.58 from a completely different direction.** That entry
measures the mid-ballot SEAT forecast as too narrow on a fixed calibration
population (`sd(z)` 1.940 at ranks 4-12). This one measures the θ PRIOR as
1.7–2.2× too narrow across the sizes that produce those seats. Two instruments,
different data, different statistics, same band, same direction. Neither is
evidence for the other, but the model's largest unexplained fault now has a
mechanism-level candidate that is not the within-pool Dirichlet.

### Cross-check

Pooled forward residual sd **0.7335**, against §1.43's independently computed
forward-validation RMSE of **0.7150** for the same estimator family — two
different computations agreeing to about 2.5%. §1.43's finding that the θ
estimator is near its ceiling on the CENTRE is untouched; this is about the
WIDTH, which §1.43 did not measure.

### And a caught error worth recording

The first version of `theta_residual` rebuilt `levels.sd_for` outside its
closure, because `sd_for` is defined inside `theta_prior` and cannot be called
from anywhere else. **It was wrong**: `sd_for` regresses squared deviation on
`baseline.get(party)` — the party's size at the TARGET — and the rebuild fed it
each party's historical sizes. Different line: 0.530 against the model's 0.150
at 0.1% of the vote. `tests/test_levels_dispersion.py` was written before the
first run and caught it immediately; the module now takes both the centre and
the width from `theta_prior` and rebuilds nothing. **A second copy of a
calculation is this repository's most reliable defect** — `MACHINERY.md`
describing a dead level layer, `build_interactive` reimplementing a replaced
drawer, the published page driving a deleted lever — and it very nearly produced
a fourth instance inside the instrument written to check one of the others.

### Disposition

- **Nothing in the model is changed by this entry.** It is a measurement.
- `SD_FLOOR` moves to 🟢 for parties at or above 15%, with the interval quoted.
- The register gains the second finding against `sd_for`'s functional form,
  at 🔴: the fit is outside the measured interval for every size below 15%.
- **The successor is a refit, not a new constant.** `sd_for` fits deviations
  from the COMMON centre; the quantity it should estimate is the residual about
  the SHRUNK centre, which is what this module computes. Fitting it that way is
  a fit to the RECORD, forward validated, not to the scoreboard — so rule 10
  permits it. It must be validated fit-one-cycle-apply-the-other, and it will
  widen the mid-ballot, which on §1.58's reading is the right direction and on
  the CRPS scoreboard will look like the wrong one.

---

## 1.60 The live forecast had an unnamed assumption about who stands. It now has a named one. (2026-08-20)

§1.47 replaced `pa_contestation_uplift` with a measured contestation correction
and recorded a −10 coherent seat gain. §1.56 then confirmed as a code fact what
that entry did not draw out: `levels.contestation` reads who stood from
`CALENDAR[target.year].results`, `CALENDAR["2026"].results` is `None`, so the
correction is **the identity on the published forecast** and the −10 was measured
with an input the live forecast does not have.

The identity is not "no assumption". It is the assumption that **every party
fields exactly the slate it fielded five years ago**, made by omission. This
entry makes it a number someone chose.

### The projection

`levels.projected_contestation`: `now = was + expand · (1 − was)`. Each party
moves that fraction of the way from its previous slate to a full one, so a party
that stood in 38% of wards gains far more than one already at 95%. The asymmetry
is the point — `blended_centres` applies contestation as the CHANGE `now / was`,
and a uniform multiplier is the same change for everyone and therefore carries no
information.

### The default is measured, and the alternative reading is why it is a lever

Every consecutive LGE pair on disk, eight metros, parties present at both
(n=165): the median party moves **+0.220** of the way to a full slate and
**65.5% expand**. Per-metro medians for the most recent transition alone
(2016→2021) are +0.46, +0.14, +0.78, +0.59, +0.63, +0.20, +0.71, +0.06 — about
**+0.5**, which is what a fragmenting party system looks like and which the 2026
forecast has as much claim to as the pooled figure.

0.220 ships as the conservative reading. That two defensible numbers differ by
more than a factor of two is exactly why this is exposed rather than typed.

### What it does, and it does it where the mechanism says it should

Johannesburg 2026, 1200 draws, median seats:

| `contestation_expand` | 0.0 (the old identity) | **0.220** | 0.5 |
|---|---|---|---|
| DA | 83 | 81.5 | 80 |
| ANC | 62 | 61 | 60 |
| **PA** | **17** | **19** | **22** |
| PA mean ward wins | 4.03 | 6.00 | **8.61** |
| ASA | 25 | 24 | 24 |

The PA stood in 52 of 135 Johannesburg wards in 2021 — the thin slate on the
ballot — and it is the party that moves. The parties already near a full slate
give up a seat or two to it. Nothing else shifts.

### Backtests are bit-identical at any value, and that is the whole hazard

Every backtestable target has published results, so `contestation` returns real
lists, `projected_contestation` is never called, and the lever cannot move a
backtest. Verified: nine city-years, 1500 draws, **254 coherent / CRPS 232.9 and
seat-identical to the committed artefact**.

**This is the same shape as `pa_contestation_uplift`** — a constant live only
where no backtest reaches, which is how that one survived for weeks. The
differences are deliberate and they are the reason this is acceptable where that
was not:

- it is **declared** in `DEFAULTS`, registered at 🔴, and named in the run's
  `note_constant` output and its verbose line, which now say *which path fired*;
- its default is **measured against the record**, not chosen for one party;
- it applies to **every party** by one rule, rather than one party by name;
- it is **superseded by data**: the moment the IEC publishes 2026 candidate
  lists and task A4 ingests them, `contestation` returns them, the projection is
  not called and the lever is inert. `tests/test_levers_are_live.py` carries it
  in `EXPECTED_INERT` with that reason;
- and it is **labelled argued-not-tested wherever quoted**, which `CLAUDE.md`
  requires and which `pa_contestation_uplift` never was.

It stays 🔴 despite the measured default, because no backtest can score it. A
measured input to an untestable branch is still an untestable branch.

---

## 1.61 PRE-REGISTRATION — how the `sd_for` refit will be judged, written before it is run (2026-08-20)

Written and committed **before** the measurement exists, because ITERATING rule
11 says a specification choice must be nested and because §1.58 established that
the obvious scoreboard statistic will point the wrong way: **CRPS falls
monotonically as the forecast narrows, all the way to a 16-fold concentration,
while coherent seat error stays flat.** A wider mid-ballot is what §1.59 says is
correct and what CRPS will call worse. If the rule is chosen after seeing the
result, it will be chosen to suit it.

Nothing here is adopted by running it. This entry fixes what would count.

### The question

`levels.sd_for` fits `(log r − mu_all)²` — squared deviation from the COMMON
centre — and hands the result to a layer whose actual residual is about the
SHRUNK centre. §1.59 measures the gap: correct at ≥15% of the vote, **1.7× to
3.5× too narrow in all four bins below it, with the cluster-bootstrap interval
excluding the model's width in every one**.

Form **A** is the committed estimator. Form **B** refits the same straight line
on leave-one-out residuals about the shrunk centre — the quantity the layer
actually faces.

### Stage 1 — selection, offline, and it does not touch the scoreboard

Both forms are fitted on the θ record and scored on **held-out θ residuals**,
never on seats. The score is the out-of-sample negative log-likelihood of the
residuals under `N(0, w²)`:

    NLL = Σ [ log w_i + r_i² / (2 w_i²) ]

a proper scoring rule for dispersion, so it cannot be gamed by widening or
narrowing alone. Lower is better.

Nested, as rule 11 requires:

* fit the form on targets **2006 + 2011 + 2016**, predict **2021**, score;
* fit on **2006 + 2011 + 2021**, predict **2016**, score;
* report both, and the per-metro-year split, since the clusters are metro-years.

**Form B proceeds to stage 2 only if it beats form A on held-out NLL in BOTH
directions.** One-of-two is a coin flip on two folds and is recorded as
undetermined.

### Stage 2 — scoring, on the scoreboard, and only on the held-out target

If B survives stage 1 it is wired in unchanged and `compare_history` is run.
**The scoreboard is quoted only for the city-years whose target was held out of
the fit** — 2021 for the fit that never saw 2021. Quoting all nine would be
quoting the score on data the form was chosen with, which is the whole of rule
11.

Reported on the **`reference`** population (§1.56), never `claimed`:

| statistic | what it must do |
|---|---|
| `sd(z)`, ranks 4-12 | move **toward 1.0** from 1.940 |
| `IQR-sd`, ranks 4-12 | move **toward 1.0** from 0.595 |
| probit-SD, ranks 1-3 | must not fall below **0.60** (it is 0.682 and already too wide) |
| coherent seats, held-out city-years | must not worsen by more than **6** |
| CRPS | **reported and explicitly not decisive** — see above |
| `p_any` for parties that won seats | no party that won a seat may drop below 0.02 |

### What would make this fail, stated now

* **B loses stage 1 in either direction** → the current form is not the fault and
  §1.59's second finding is about the bins rather than the line. Stop.
* **B wins stage 1 and the two width statistics move in opposite directions** →
  the band is mis-shaped rather than mis-scaled (§1.58) and a refitted line
  cannot fix it either. Record and stop; the object is then A2's mixture.
* **B wins stage 1, widths improve, and coherent seats worsen by more than 6 on
  the held-out city-years** → do not ship. Worse does not ship, and a width
  improvement bought with seats is the trade §1.54 already refused once.
* **Everything improves** → still not adopted on this entry alone. Two folds on
  a panel with about two effective cycle clusters (rule 11) can detect a large
  effect and nothing else. **An improvement smaller than the draw noise the
  protocol already quotes (±2 to ±4 coherent seats) is UNDETERMINED, not
  adopted.**

### And the standing caveat

Eight of the nine scoreboard city-years are one cycle. Stage 2 can therefore
distinguish "this is a better estimator" from "this suits 2021" only weakly, and
the 2016 direction is a single city. Stage 1 is the load-bearing test — 257
observations across 18 metro-year clusters — and stage 2 is a check that the
gain survives contact with the rest of the machinery, not an independent
confirmation.

---

## 1.62 The `sd_for` refit is refuted, and the pre-registration is why that is a result (2026-08-20)

**Negative result. No model change. `levels.sd_for` stands exactly as committed.**

§1.59 measured the committed θ dispersion as 1.7× to 3.5× too narrow below 15%
of the vote, with the cluster-bootstrap interval excluding it in all four bins.
§1.61 pre-registered how a refit would be judged, before building one, because
§1.58 had established that CRPS would call the correct change worse. Stage 1 was
run. Both refits fail it.

### Stage 1 — held-out NLL, mean per observation, lower is better

Coefficients are fitted from the record strictly before each target, as the
model does; the score is `Σ[log w + r²/(2w²)]` on that target's realised
residuals — proper for dispersion, so neither widening nor narrowing alone can
win it.

| target | n | metro-years | **A** (committed) | **B** (refit, leave-one-observation-out) | **C** (refit, leave-one-cycle-out) |
|---|---|---|---|---|---|
| 2016 | 97 | 8 | 1.1929 | 2.0657 | **0.6815** |
| 2021 | 138 | 8 | **0.1611** | 1.4948 | 0.9822 |

*(2006 and 2011 carry 11 observations from one metro each — the pre-2011 archive
is Johannesburg only — and `size_centre` needs 20, so neither refit can be
formed there. The comparison is the two folds §1.61 named.)*

**B loses both folds. C wins one and loses one.** §1.61's rule: *"one-of-two is
a coin flip on two folds and is recorded as undetermined."* Neither reaches
stage 2, and the scoreboard was never run.

### Why B failed, which is the reusable part

B fitted dispersions that were **too narrow** — the opposite of the fault it was
built to fix. Leave-one-observation-out was not leaving out anything much: a
party's observations cluster by CYCLE, so dropping the ANC's 2016 Johannesburg
ratio leaves its 2016 ratios in seven other metros, all sharing the 2016 national
swing, still setting the centre it is scored against. Measured directly:

| | leave-one-observation-out, inside the record | genuine forward residual |
|---|---|---|
| 2016 | 0.589 | 0.724 |
| 2021 | 0.555 | 0.705 |

Understated by **1.23× and 1.27×**, in the same direction both times. This is
ITERATING rule 11's clustering point one level down: *the unit you leave out has
to be the unit the shocks arrive in.* C leaves out the cycle and does close most
of that gap — its 2016 fold is the best number in the table — which confirms the
diagnosis without rescuing the change.

### What it means for §1.59, and it is not that §1.59 was wrong

§1.59's measurement stands: the committed fit really is 1.7× to 3.5× adrift of
the conditional dispersion below 15% of the vote. What is now refuted is the
proposed CAUSE — that it fits the wrong residual. Fitting the right residual, by
either construction, predicts held-out dispersion no better and usually worse.

The remaining explanation is the one §1.59 named second and this entry promotes
to first: **the measured conditional dispersion is not monotone in size** —
0.915, 0.737, 0.448, 0.663, 0.138 — and a straight line in log(size) cannot be
right in the middle and at both ends whatever it is fitted to. The fault is the
FORM, not the residual. §1.61 anticipated exactly this and called it: *"the
current form is not the fault and §1.59's second finding is about the bins rather
than the line."*

### The trial budget, stated because it is the thing that would go wrong next

Two forms have now been tested on two folds. A third, fourth and fifth would
eventually produce one that wins both by luck: two folds is roughly a coin flip
per trial, so a handful of attempts makes a spurious two-of-two likely. **No
further functional form should be tried against these two folds.** A non-monotone
form is the obvious next idea and it is precisely the one that must NOT be tried
here — it has more freedom and fewer constraints, and the panel cannot tell a
real non-monotonicity from the 14 observations sitting in the 5–15% bin.

What would license another attempt: more folds (the θ record can be extended
backwards if the pre-2011 archive is ingested for the other seven metros), or a
mechanism argument that names the shape in advance rather than reading it off
the bins.

### And the pre-registration earned its keep on the first use

C's 2016 fold is the best single number in the table. Without §1.61 committed
beforehand, the honest-looking move would have been to quote that fold, describe
the 2021 fold as noise, and ship a change that is a coin flip. The rule was
written down first, it said one-of-two is undetermined, and it decided this.

---

## 1.63 The arrival-group mechanism was not off. It was unreachable, and broken. (2026-08-20)

The model's largest single error class is arrivals and surges — 130 of 1,752
seats across the panel, with the model giving a median seat to one arrival in
thirty-two. There are two mechanisms for it: the generic `ENTRANT` slot, a
Bernoulli times a triangular, and the ARRIVAL-GROUP draw, a group total from a
fitted lognormal split among named arrivals by a Dirichlet weighted on ward
reach. The second is far better motivated, is fully implemented, has an emitted
spec, and carries a recorded measurement and a scheduled retry.

**None of it could run.** Three separate faults, each hiding the next.

### 1. The switch did not exist

`blended_centres` reads `scenario.get("arrival_group_draw")`. That key was in no
`DEFAULTS`, so it was always `None`. `parse_set` raises `SystemExit` on a key
that is not already in the scenario, and `read_scenario_file` rejects unknown
keys against `DEFAULTS`, so **`--set` and a config file could not create it
either**. No city toml declares it. The mechanism was unreachable by every
supported route.

`MACHINERY.md` listed it among the *switched-off* levers, which claims a switch.
The `DEFAULTS`-adjacent code comment says "DEFAULT OFF", which claims a default.
There was neither.

This is the same class as `LEVEL_DF` bound as a default argument (§1.33) and
`polling_lean` passed to a function that never read it. It escaped
`test_every_defaults_key_is_swept_or_excused` and
`test_every_tunable_lever_actually_moves_the_forecast` for the one reason
neither can catch: **both iterate `DEFAULTS`, and this was not in it.** A lever
guard keyed on the register cannot see a lever missing from the register.

### 2. It was broken

Declared and switched on, the branch raised

    NameError: name 'dirichlet_floor' is not defined

on its first line of real work. The variable in scope is `mean_floor`; the name
was changed and this branch was not, because nothing could reach it to fail.

Two consequences worth stating. The rejection measurement recorded against this
mechanism (*"Johannesburg 2021 CRPS 85.9 → 109.9"*) was taken on code that has
since drifted, so it is a measurement of something that is no longer here. And
the code comment scheduling a retry — *"by 2026 the record includes 2021 …
retry it then"* — **scheduled a crash**.

### 3. And at 2026 it is gated on data that does not exist

`pools.arrival_group_spec` returns `None` unless the target has a real roster:
it splits the group total by each named arrival's ward reach, and there are no
named arrivals until nomination lists close. Its own docstring says so. Confirmed
in the emitted specs — `arrival_group` is present in `pools_2021.json` with 32
members and **absent from `pools_2026.json` and `pools_2016.json`**.

So the retry the comment scheduled for 2026 could not have been run even with
the other two faults fixed. The IEC publishes the final 2026 candidate list on
**16 September 2026** (nominations closed 28 August, polling 4 November).

### Measured on nine city-years, which the rejection never was

Declared, repaired, and swept. The original rejection was Johannesburg only:

| city-year | off | ON | delta |
|---|---|---|---|
| Johannesburg 2016 | 16 | 16 | — *(no spec)* |
| Johannesburg 2021 | 86 | 114 | **+28** |
| Tshwane 2021 | 30 | 56 | **+26** |
| Ekurhuleni 2021 | 18 | 46 | **+28** |
| eThekwini 2021 | 32 | 38 | +6 |
| Cape Town 2021 | 34 | 40 | +6 |
| Mangaung 2021 | 10 | 8 | −2 |
| Nelson Mandela Bay 2021 | 18 | 20 | +2 |
| Buffalo City 2021 | 10 | 10 | — |
| **total coherent** | **254** | **348** | **+94** |
| **total CRPS** | **232.9** | **296.0** | **+63.1** |

**The rejection is confirmed and strengthened.** Worse in six city-years, better
in one, and the effect is far outside draw noise.

It is also the same failure everywhere, which is the original reason generalised:
the eight scored metros are all 2021, their group total is fitted on 2016 alone
(metro-years 0.31%–4.74%, median 1.57%), and 2021 came in at 19.99%. No honest
draw from that record reaches it. The mechanism forecasts what the record says
and the record was superseded — in every metro, not just Johannesburg.

### Disposition, and what it says about the retry

- `arrival_group_draw` is now **declared in `DEFAULTS` at `False`**, registered,
  swept, and carried in `EXPECTED_INERT` at 2026 with the data gate as its
  reason. What changed is that "off" is true rather than merely written down.
- The `NameError` is fixed. **No live number moves**: the default path is
  seat-identical to the committed artefact, 254 coherent / CRPS 232.9.
- **The retry condition as written cannot be tested.** It asks for "a target
  whose prior cycle is not a regime change", and the only such target is 2026,
  which is not scorable and has no spec until the lists land. Any 2026 adoption
  would be a mechanism live exactly where nothing can check it — the
  `pa_contestation_uplift` and `w_bye` position — and must be labelled that way
  if it is ever taken.
- **This raises A4's value.** The 16 September candidate lists unblock three
  things at once: the contestation correction (currently the identity on the
  live forecast, §1.56), the projection standing in for it (`contestation_expand`
  goes inert, §1.60), and this mechanism's 2026 spec.

### The guard that would have caught it

None of the three faults is visible to a lever guard that iterates `DEFAULTS`.
What is needed is the complement: **every `scenario.get("…")` in `montecarlo.py`
whose key is not in `DEFAULTS`** — a key read but never declared is either dead
or a typo, and both are silent. Not built here; recorded as the specific test
this entry argues for.

---

## 1.64 The ingest is externally validated to the vote, and the two things we cannot see (2026-08-21)

`inside-politics.org` — Gareth van Onselen's series on Election 2026/7 — is the
closest thing to a competitor working the same ground. **It is not a forecasting
model**: it publishes ward-level choropleths, turnout tracks and qualitative
analysis, and it makes no seat projection and no probabilistic forecast. So there
is no forecast to score against. What it does publish is hard numbers computed
independently from the same IEC source, and those are a better check than a rival
forecast would be, because a disagreement would be a fact about the DATA rather
than about two sets of assumptions.

### Checked, and it matches to the individual vote

Johannesburg 2021, from *"Action South Africa's prospects in JHB"* (17 Feb 2026):

| | theirs | ours |
|---|---|---|
| ASA PR votes | 167,359 | **167,359** |
| ASA ward votes | 128,986 | **128,986** |
| PR excess | +38,373 | **+38,373** |
| as a share of PR | 23% | 22.9% |
| ASA citywide PR share | 18.12% | **18.12%** |

And the ward-level distribution, which tests the VD→ward mapping rather than a
citywide total — ASA's PR share in each of the 135 wards:

| | 0-5% | 5-10% | 10-15% | 15-20% | 20-25% | 25%+ |
|---|---|---|---|---|---|---|
| theirs | 1 | 19 | 16 | 50 | 33 | 16 |
| **ours** | **1** | **19** | **16** | **50** | **33** | **16** |

Exact in all six bands. It also settles an ambiguity in their write-up: the
distribution is the **PR** ballot, not the ward ballot (the ward ballot gives 6 /
27 / 48 / 40 / 10 / 4).

`DATA-QUALITY.md` records the traps that corrupt an IEC ingest silently. This is
the first check of the ingest against a party outside this project, and it
passes.

### It also incidentally clears a suspected defect

Their figures imply ASA's true 2021 ward/PR ratio is **0.7707**, and the run at
target 2021 prints **0.81**. That is not an error: ASA is an ARRIVAL at 2021 with
no prior local record, so 0.81 is the fallback and the model cannot know 0.77
without reading its own answer. At target **2026**, where 2021 is history, the
run prints **0.77** — the measured value. Both targets are doing the right thing.

### The two things they have that the model cannot see

Neither is a data-ingest gap. Both are inputs with no channel in the model at
all, and they are recorded here so that "we have everything they have" is not
quoted without them.

1. **Announced contestation, ahead of nomination lists.** They report ASA
   standing in about **42 municipalities** in 2026, gathered from the party's own
   statements months before nominations closed. The model has no path for
   announced-but-not-filed intent; `levels.contestation` reads filed lists, and
   §1.60's `contestation_expand` projects from 2021 rather than from what parties
   have said. This is soft data and it is not obvious it should be ingested — but
   it is data, it bears on the one input the live forecast is missing, and it was
   available in February.

2. **Who the mayoral candidate is.** Helen Zille is the DA's Johannesburg
   candidate, and their argument is specific: she suppresses ASA in particular,
   by neutralising Mashaba's appeal among potential DA voters. **The model has no
   candidate term of any kind.** The effect is measurable in principle and partly
   already in our inputs — ASA's +38,373 PR excess is 23% of its PR vote and runs
   the OPPOSITE way to the ANC's and DA's, whose differentials favour the ward
   ballot, which is what a party carried by its mayoral candidate looks like.
   `levels.ward_pr_ratios` already carries that number per party (ASA 0.77). What
   is missing is any reason for it to CHANGE when the candidate changes, and
   nothing in four cycles identifies that.

Recorded as a named blind spot rather than a task: with one ASA local election on
record, a candidate effect cannot be estimated from this archive, and inventing
one would be a party-specific constant of exactly the kind deleted twice
(§1.47).

---

## 1.65 The poll channel is worth 50 coherent seats, and nobody had ever measured it (2026-08-21)

`src/polling.py` has been in the model since 2026-08-14, is the best-argued
module in the repository, and **had never been scored**. `sweep.py` contains the
string "poll" zero times; `compare_history` has no poll column; `backtest`
declares both paths leak-free with empty year tuples, which is a statement about
leakage rather than about skill. The one test that touches it asserts the branch
*runs*, not that it helps.

The obstacle was that there was no way to switch it off short of emptying
`polls.json`. `poll_paths` is that switch — `"off"` | `"arrivals"` | `"all"` —
and with it the channel is measurable for the first time.

### Nine city-years, 1500 draws, coherent seat error

| city-year | off | arrivals | all |
|---|---|---|---|
| Johannesburg 2016 | 18 | 18 | **16** |
| Johannesburg 2021 | 90 | **86** | 86 |
| **Tshwane 2021** | 52 | **30** | 30 |
| **Ekurhuleni 2021** | 38 | **18** | 18 |
| eThekwini 2021 | 34 | **32** | 32 |
| Cape Town 2021 | 34 | 34 | 34 |
| Mangaung 2021 | 10 | 10 | 10 |
| Nelson Mandela Bay 2021 | 18 | 18 | 18 |
| Buffalo City 2021 | 10 | 10 | 10 |
| **total coherent** | **304** | **256** | **254** |
| **total CRPS** | **263.7** | **232.7** | **232.9** |

**The arrivals path is worth 48 coherent seats and 31.0 CRPS**, which puts it
alongside the level shrink (312 → 264, §1.44) as one of the two largest effects
ever measured here. The metro path adds two more, entirely at Johannesburg 2016,
the one city-year it fires on. **No city-year is made worse by either.**

### It refutes the prediction made before running it

The plan written that morning said to *"expect Johannesburg 2021 to look like a
regression"*: `poll_levels` outranks the arrival seed, the seed puts ActionSA at
11.07%, the contested-area conversion gives ~6.3%, and the actual was 16.05%, so
replacing a closer number with a further one should cost seats.

It does not. Johannesburg 2021 **improves**, 90 → 86. And the effect is not
where the argument put it at all — it is at **Tshwane (−22)** and **Ekurhuleni
(−20)**, where ActionSA's actual was far lower than in Johannesburg and ~6.3% is
close, while Johannesburg's own gain is the smallest of the four. The prediction
had the right mechanism and the wrong sign, because it reasoned about the metro
the model is worst at instead of about the four the path actually touches.

### A temporal leak, found in the path and measured to be inert

`_stood` decided which metros a party contested by asking where it got **votes**
at the target:

    _stood = [c for c in METRO_CODES
              if metro_citywide(c, target.year).get(party, 0.0) > 0]

That reads the result the backtest is predicting. Row existence is the
nomination fact and reading it does not touch the outcome — the argument
`levels.contestation` already runs on (§1.47) — so `pools.metro_roster` replaces
it.

**Measured before the change rather than after, so the correction cannot be
mistaken for a result.** The two definitions agree for every party the poll path
touches: ActionSA's roster and its vote-presence are the same four metros at 2021
(JHB, TSH, EKU, ETH) and both empty at 2016. They differ only for Al Jama-ah — a
row in Ekurhuleni, no votes there — and Al Jama-ah has a baseline, so the path
skips it. Closing the leak is **seat-identical**: 254 coherent / CRPS 232.9, every
city-year unchanged.

So the leak was real, and it was inert. The 48 seats are not leakage.

### What this does NOT establish

- **Eight of the nine city-years are one cycle**, and the entire arrivals effect
  is one party — ActionSA — in four metros of that cycle. Under ITERATING rule
  11 the effective sample here is close to one. This is a large effect with a
  clear mechanism, not a well-identified one.
- **The path is dead at 2026.** `NATIONAL_VOTES` has no `"2026"` key, so
  `contested_share` returns `None` and the conversion cannot run. **The 48 seats
  are measured on a channel the live forecast does not currently have** — the
  same position §1.56 found the contestation correction in, and it must be said
  wherever this number is quoted.
- The contested-area denominator still covers only the **eight metros**, not the
  ~213 municipalities the national poll's denominator spans. That is a known
  approximation in `polling.metro_estimate` and it is unchanged here.

### Disposition

- `poll_paths` ships at `"all"`, which is the committed behaviour: the run at
  `"all"` is seat-identical to the committed artefact.
- The leak is closed. `pools.metro_roster` carries the measurement in its
  docstring so the next reader does not have to redo it.
- **This raises the value of a 2026 `NATIONAL_VOTES` entry** — roll × projected
  turnout — since without it the largest measured contribution in the poll
  channel is switched off for the election we are actually forecasting.

---

## 1.66 Two poll claims audited: one holds, one is a tautology dressed as a result (2026-08-22)

`src/polling.py` carried two measurements that **no script in the repository
produced** and that appeared in no MODEL-LOG entry. Both were checked before the
module is rewritten, because a rewrite would have buried them.

### The stale-poll rule — HOLDS, and costs more than it claimed

`usable_for` refuses a poll declared for a different election. The comment
justifies it with *"Johannesburg 2021 CRPS 77.0 → 86.2"*. Re-measured by
removing the declaration filter so `ipsos-2016-lge-joburg` — five years stale —
can inform the 2021 forecast:

| | CRPS | coherent |
|---|---|---|
| rule ON (committed) | **66.4** | **86** |
| rule OFF, 2016 poll admitted | 76.4 | 94 |

The absolute levels have moved because the model has improved since (the
baseline really was 77.0 then), but **the effect reproduces almost exactly**:
+10.0 CRPS today against the +9.2 recorded, and **+8 coherent seats the original
claim did not mention**. The rule is worth more than its own comment says.

### The contested-area table — reproduces exactly, and shows less than it appears to

    2016 (83 arrivals)   raw 1.609   adjusted 0.000
    2021 (175 arrivals)  raw 1.228   adjusted 0.144

Every figure is right, to three decimals, including the arrival counts —
`src/contested_area.py` now produces it. Reproducing it turned up three things
the table does not say.

**1. It is largely a tautology.** A party standing in ONE metro has an estimate
that is exact *by identity*: its share of its contested area is its share of that
metro. Such an arrival contributes a hard zero.

| | single-metro arrivals | multi-metro median |
|---|---|---|
| 2016 | **46 of 83 (55%)** | 0.234 |
| 2021 | **67 of 175 (38%)** | **0.431** |

At 2016 the majority are single-metro, so the median *is* one of those zeros —
which the docstring concedes as "trivially exact", while treating the 2021 figure
beside it as a real result built from the same material. **On multi-metro
arrivals, the only cases where the conversion does any work, it is 0.431 — a
factor of 1.54, three times the 0.144 quoted.**

**2. The two columns use different denominators.** "raw" is the party's share of
the eight-metro aggregate; "adjusted" runs through `contested_share`, whose
denominator is national. Against a consistent national denominator raw is 2.504
and 1.995. So part of the displayed improvement is a change of denominator, not
the adjustment.

**3. And it does not test the conversion it appears to.** In the table `X` is
reconstructed from the archive, so the national figure **cancels** and the
estimate reduces to

    total votes / votes cast in the metros the party stood in

— the party's share of its own contested area, computed entirely inside the
metro archive. The poll never appears and neither does `NATIONAL_VOTES`. So it
validates the **geographic** half of the mechanism and not the **conversion**
half, which is the half that runs in production and the half `NATIONAL_VOTES`
exists for.

### Disposition

- Both claims corrected in place in `polling.py`; neither deleted, because the
  measurement that was wrong about its own scope is the more useful record.
- `src/contested_area.py` is committed so the table cannot drift again.
- **What actually validates this mechanism is §1.65** — the real poll, the real
  path, 48 coherent seats over nine city-years. The table is the weaker
  companion and should be quoted as one.
- The pattern is now three for three: §1.59's `SD_FLOOR`, §1.63's dead
  `arrival_group_draw` comment, and this. **A number in a docstring with no
  script behind it has been wrong or overstated every time it has been checked.**
  That is the argument for the Phase 3 provenance work, one layer down from the
  published page.

---

## 1.67 σ_poll becomes a decomposition, and one house is capped at 0.42 (2026-08-22)

§1.65 established that the poll channel is worth 48 coherent seats. This is the
other half: **how much a poll should count**, rewritten before the first real
2026 numbers move a published forecast.

### What was wrong

`POLL_RMS_ERROR = 0.030` was applied flat to every poll of every party. It is a
good number — the RMS of Ipsos's nine 2016 metro readings, a track record rather
than a nominal margin — and it was measured on **full-sample metro polls, by one
house, two days before polling day**. Both admitted 2026 polls are ~500-person
subsamples of a national sample, a different house, an undisclosed likely-voter
screen, months out. `n` was recorded on every poll and **read by nothing**. And
there was no cap: ten waves of one house would each have blended at w≈0.9.

### The decomposition, which preserves the measurement rather than discarding it

    σ_poll² = deff·p̂(1−p̂)/n  +  σ_house²  +  σ_screen²  +  (drift·√days)²

`POLL_HOUSE_SD` is not a new guess — it is the 3.03pp track record with the
sampling term removed, and it is robust to the one thing we do not know:

| assumed n | mean sampling | residual → `POLL_HOUSE_SD` |
|---|---|---|
| 500 | 2.13pp | 2.16pp |
| 800 | 1.68pp | **2.52pp** |
| 1500 | 1.23pp | 2.77pp |

**Screen and drift are EXCESS terms, and that is the trap in the arithmetic.**
The 2.5pp residual is the *total* non-sampling error of polls whose method was
public and which had two days of drift, so their screen error is already inside
it. Charging every poll a screen term on top counts it twice. Both are therefore
measured as an excess over the calibration case: zero for a disclosed screen,
zero at zero days out. The design this was built from added them unconditionally;
that was caught here rather than shipped.

**The self-consistency check**: run the calibration polls back through and the
decomposition returns **3.05pp against 3.03pp** — 0.02pp. That is what licenses
`POLL_HOUSE_SD` as measured, and `tests/test_polling_sd.py` asserts it.

Applied to the July 2026 SRF wave (p̂ 0.42, n 504, deff 1.6, undisclosed screen,
96 days out): sampling 2.78 · house 2.50 · screen 2.00 · drift 0.98 → **4.35pp**,
against 3.00pp before. And `n_eff = 504/1.6 = 315`, i.e. ±5.5pp — not the ±4.4pp
the record's own caveat string claims.

### One house has a floor it cannot publish its way past

House error is a bias every wave of a house shares, so the aggregate shrinks
sampling with **waves** and house error only with **houses** — `σ_house²/H_eff`,
where `H_eff` is the Kish effective house count.

| waves of one house | 1 | 2 | 4 | 8 | 20 | 100 |
|---|---|---|---|---|---|---|
| σ_aggregate | 4.35 | 3.88 | 3.63 | 3.49 | 3.41 | **3.36pp** |

against an irreducible **3.35pp**. An earlier draft of this argument claimed two
waves "buy nothing"; measured, they buy 4.35 → 3.88 — a real reduction in the
sampling term and none at all in the house term. **The protection is the
asymptote, not a flat line**, and saying so is the difference between an argument
and a measurement.

### And on top of it, a cap on house diversity

    w_cap(H) = H / (H + poll_house_k)     1 → 0.50   2 → 0.67   3 → 0.75

Because inverse variance is only correct if both estimates are **unbiased**, and
one house with an undisclosed screen is exactly where the bias term is unbounded
and no variance formula can express it. The same `m/(k+m)` shape the spine and
`POLL_K` already use; the asymptote is 1.0 *by argument*, so it costs one
declared number.

**Where it binds today.** At Johannesburg 2026 the DA's inverse-variance weight
is 0.560 and it is held to **0.500** — not because of anything about the DA, but
because `H_eff = 1.0` and only one house has published. The ANC's 0.498 passes
through untouched. If a second independent house published, `H_eff` rises to
1.94, the cap loosens to 0.66, and precision binds instead. **The lever that
unlocks it is real-world, not code.**

Independent corroboration that this is the right risk to price, rather than our
own suspicion: the Daily Maverick (2026-08-17) notes that SRF's staff and those
of its service provider Victory Research *"have had close associations with the
DA"*.

### Measured

**The backtest barely moves: 254 coherent, unchanged city-year by city-year;
CRPS 232.93 → 232.73, entirely at Johannesburg 2016** (18.93 → 18.73), the one
city-year the metro path fires on. Seat counts there are identical; the
distribution tightens slightly.

> **A stale figure, caught and corrected the next day.** This paragraph first
> read "CRPS 232.9 → 232.8, identical city-year by city-year". That measurement
> was taken at `poll_house_k = 1.4`, and the entry then shipped **1.0** — so the
> number quoted was for a configuration that was never committed. Found by
> §1.68 asking why a supposedly inert change had moved CRPS, and isolated by
> re-running with `--set poll_house_k=1.4`, which reproduces 232.82
> **seat-identically**. Measure the thing you ship, not the thing you measured
> on the way to it.

And the reason the movement is so small is worth stating rather than celebrating —
**the only poll any backtest sees is Johannesburg 2016's, which IS the
calibration poll**: full sample, disclosed method, two days out. The
decomposition is inert there by construction. So this change is live exactly
where nothing can check it, the `w_bye` and `contestation_expand` position, and
must be labelled that way wherever quoted.

Where it does act — Johannesburg 2026, 1200 draws, median seats:

| | flat 3.0pp, no cap | decomposed + cap | |
|---|---|---|---|
| **DA** | **83** | **77** | **−6** |
| ANC | 58 | 59 | +1 |
| ASA | 26 | 27 | +1 |
| MK | 25 | 26 | +1 |
| EFF | 25 | 26 | +1 |
| PA | 20 | 21 | +1 |

Six seats off the DA, because a DA-adjacent house's reading of DA 41.1% was
taking 0.67 of the blend and now takes 0.42.

### Stress-tested on synthetic polls, because two real ones cannot find a bug

The register holds two admitted 2026 polls: same house, same size, same method.
Every property the scheme depends on is unexercised by them.
`tests/test_polling_synthetic.py` drives made-up polls inside plausible metro
bounds through the real arithmetic and asserts eight properties — a second house
is worth more than a second wave; a million respondents cannot break the floor
or the cap; a poll agreeing with the model moves it nothing; a poll disagreeing
moves it toward and not past; more waves approach the floor and never cross;
hiding a screen costs something; a stale poll is priced worse; a subsample is
priced as a subsample.

**These are not only a convenience.** Once readers submit polls to the
competition the weighting is an untrusted-input surface, and a poll claiming a
million respondents is an *expected* input. Those assertions are the bound on
what a reader can do to the published forecast.

### Every judgement call in it is adjustable, and that is not a detail

`poll_house_k`, `poll_deff_subsample`, `poll_screen_sd`,
`poll_drift_per_root_day` and `poll_half_life_days` are all `DEFAULTS` keys,
reachable from `--set`, a config file, the sweep and the interactive.

**Because a judgement call nobody can move is indistinguishable from a fact** —
and this entry contains the proof. `POLL_HOUSE_K` shipped at **1.4**, putting the
cap at 0.42, for no reason anyone could check; asked why 0.42, there was no
answer. It is now **1.0**, giving exactly 0.50, on a rule that can be stated in a
sentence: *a single unreplicated house is never worth more than the model
itself.* That is not more measured — it is more explicable, and it is the value
`SPINE_K` and `POLL_K` already carry. `--set poll_house_k=1.4` reproduces the
old behaviour exactly.

The difference is not cosmetic. At 1.4 the cap overrode the variance arithmetic
for the ANC as well as the DA — 0.498 and 0.560 both pulled to 0.42. At 1.0 it
binds only where a poll would otherwise outweigh the model, which is the
condition a cap should exist for, and the ANC's 0.498 passes through untouched.

A tighter cap is available and deliberately not taken. There is independent
reason to think this particular house leans one way, but encoding a view about
one house in a global constant is the party-specific fiddle this project has
deleted twice. If a house needs discounting, discount that house.

### And the guard caught this entry making the exact mistake it is about

`POLL_HALF_LIFE_DAYS` was written into three signatures as
`half_life_days: float = POLL_HALF_LIFE_DAYS` — **a module constant captured in
a default argument, evaluated once at import, frozen thereafter.** That is
`LEVEL_DF` (§1.33), the defect this repository is most marked by, reintroduced
in the same commit that promotes the constant out of exactly that shape.

`test_no_numeric_module_constant_is_a_default_argument` failed on all three
before any of it shipped. Two things worth recording: the guard is worth its
runtime, and **knowing about a defect in detail is no protection against
committing it** — which is the argument for behavioural guards over careful
authors, and it is the third time this week a test has caught the author of the
entry describing the trap.

### Also fixed

`POLL_HALF_LIFE_DAYS` **did not exist**. It was registered in
`JUDGEMENT-CALLS.md` at 120 and was a default argument on `polling.aggregate`, so
no `--set` and no config file could reach it. `test_every_tunable_constant_is_in_
the_judgement_register` only checks code → register, so a register row naming a
non-existent constant passed. It is now a module constant mirrored in `DEFAULTS`
with the two asserted equal at import — and it is the second instance this week
of the register being right about a thing that was not there.

---

## 1.68 The legacy poll path is deleted, and the register stops losing records in silence (2026-08-22)

Two changes, both about a poll being used or refused **for a reason someone can
read**. Neither moves the backtest.

### The legacy path, deleted

`poll_id` / `poll_weight` / `poll_k` re-read `polls.json` directly and applied
whatever they found, **bypassing `polling.usable_for` entirely**: no
fieldwork-date check, no party-commissioned exclusion, no scope or city check,
no election-declaration rule. So

* `--set poll_id="da-internal-2026aug"` admitted the DA's own internal poll —
  the record whose own note calls it *"the evidence for the exclusion rule, not
  evidence about the election"*;
* `--set poll_id="ipsos-2016-lge-joburg"` at target 2021 admitted a five-year-
  stale poll, which §1.66 measured at **+10.0 CRPS and +8 coherent seats**.

It had also **never executed**: it referred to `prior`, a local of
`blended_centres`, so it raised `NameError` the instant `poll_weight` went above
zero. And its weight was keyed on how much θ history a party had — a second
poll-weighting implementation sitting beside the live one and disagreeing with
it, which is this repository's most reliable defect.

**Nothing is lost.** What it existed to do — let a poll speak for a party the
record cannot see — is the arrivals path, measured at 48 coherent seats (§1.65).
What it did in addition, applying an unscreened poll to every party, is the
metro path with admission rules (§1.67).

*A correction to the reasoning, not the conclusion.* An earlier statement of
this said the path had to go because **the interactive drives it**. That is
wrong: nothing in the model reads the interactive — the only channel out of that
page is a textarea a human pastes into `--config`, and `PUBLISHING-BACKLOG.md`
§1 already recorded it as inert. The three reasons above are internal to the
Python model and each is sufficient on its own.

### The register stops losing records in silence

`usable_for` expressed two entirely different things with the same `continue`:
*"this poll is about a different election"*, which is correct behaviour, and
*"someone typed `Metro` instead of `metro`"*, which is a poll we meant to count
and silently did not. Both printed nothing.

Not hypothetical: `ipsos-w2-2025-metros` is dropped by every caller **and
offered as a one-click preset by the interactive**. And the 2026 forecast rests
on one house's two waves — losing one to a typo would move a published number
and say nothing.

So the two ideas are separated:

* **`validate` / `validate_or_die`** — malformed records. Fatal. Called from
  `run_model` before the poll section, from `tests/test_polling_register.py`,
  and from `build_all.py` as step 0 so a bad record costs a second rather than
  a full build.
* **`screen`** — well-formed polls this target may not use, each returned as an
  `Exclusion` with its rule and detail. `usable_for` is now a thin wrapper, and
  a verbose run prints what it declined:

```
  polls declined (7):
      da-internal-2026aug: commissioned by Democratic Alliance [commissioned]
      ipsos-2021-lge-national: declared for 2021, not 2026 [other-election]
      ...
```

### The line between them was drawn the hard way

The first validator made a **missing sample size fatal** — and it refused the
committed register, because **Ipsos never published the metro cut sizes for the
nine 2016 readings `POLL_HOUSE_SD` is calibrated on**. A rule strict enough to
reject its own calibration set is measuring the author's wishes rather than the
data.

So `Problem` carries a severity. **"error" is malformed** — a `scope` of
`"Metro"`, shares summing to 60 because someone typed percentages, `n` below
`poll_min_n`, a metro poll with numbers and no city. **"warn" is incomplete but
honest** — a house that never published its sample size, which the arithmetic
already handles by falling back to the house term. The committed register has
**0 errors and 6 warnings**, and every warning names a real limitation.

### And the sweep guard caught the deletion halfway done

Removing the three keys from `DEFAULTS` left them in `PERTURB`, and
`test_every_defaults_key_is_swept_or_excused` failed with exactly the right
words: *"these PERTURB entries are not DEFAULTS keys, so the sweep SILENTLY
SKIPS them and reports success"*. A half-finished deletion reads as a passing
sweep, which is the failure that guard exists for. `_LEGACY_POLL`'s text is kept
even though its lever is gone, because the lesson it carries — **a null measured
with the gate shut is not a null** — is about how to measure a lever rather than
about that lever.

### Measured

Backtest **unchanged, and demonstrated rather than assumed**: the deleted path
never executed, and the validation refuses nothing the screen was not already
dropping. Verified by re-running the whole panel at `--set poll_house_k=1.4` —
the value §1.67 was measured at — which reproduces that run's 254 coherent /
CRPS 232.82 **seat-identically across all nine city-years**. So every difference
between this commit and that measurement is the `poll_house_k` change, and none
of it is this one.

That check is also how §1.67's stale CRPS figure was found: the entry quoted a
number taken at K = 1.4 and shipped K = 1.0. Corrected in place there.

`poll_min_n` joins the four judgement calls of §1.67 as a settable `DEFAULTS`
key.

---

## 1.69 An outside audit finds a red suite, a register that lies, and a panel half the size of the archive (2026-08-22)

An independent review was run from the forecaster's standpoint — instrument
first, then baseline, then where the error is, then calibration, then structure.
It is written up here because **three of its findings are defects in this
repository's own guards**, and a guard that passes while the thing it guards is
wrong is worse than no guard: it converts an absence of evidence into a claim.

### The suite was red, and every failure was the uncommitted §1.68 work

Four distinct failures, on a working tree whose model was being quoted at 254
coherent seats. `tests/test_regressions.py` is not in that diff, and
`git show HEAD:src/montecarlo.py` confirms both broken anchors existed at HEAD,
so these are regressions introduced by §1.68 and not pre-existing.

| test | cause |
|---|---|
| `test_no_clamp_is_anchored_on_the_national_baseline` | the clamp refactor removed `anchor = centres.get(party)` |
| `test_the_polling_channel_actually_runs` | still opened the channel with the deleted `poll_id` |
| `test_every_defaults_key_is_swept_or_excused` | `poll_weight` re-injected into `DEFAULTS` |
| `test_every_tunable_lever_actually_moves_the_forecast` | `poll_min_n` cannot be swept — see below |

The first two are stale tests and are rewritten. The rewrite of
`test_the_polling_channel_actually_runs` is deliberately **stronger** than what
it replaces: it drives the live path (`poll_paths`, the register, `screen`) and
asserts both that the channel runs when switched on and that switching it off
silences it. A channel that cannot be switched off cannot be measured, which is
the entire reason `poll_paths` exists (§1.65), and nothing tested that.

### `poll_min_n` was on the wrong side of the line §1.68 had just drawn

§1.68 defined the split precisely — **validate = malformed, fatal; screen =
well-formed polls this target may not use** — and then put the sample-size floor
on the fatal side. So:

* sweeping `poll_min_n` above 504, which the lever guard is *required* to do,
  raised `PollRegisterError` and killed the run. The lever could not be
  perturbed at all, and a lever that cannot be perturbed is one nobody has
  measured;
* a reader submitting a small poll to the competition would have been told
  their record was **malformed** when it was merely **small**.

A poll with a published, positive, too-small `n` is the definition of
well-formed-but-inadmissible. The floor moves to `screen` as an `under-min-n`
`Exclusion`, so it now prints its refusal with a reason like every other screen
rule. `validate` keeps the `min_n` kwarg, accepted and ignored, and is in
`DELIBERATELY_UNUSED` saying so.

Measured: at `poll_min_n=5000` the run no longer dies — it declines 9 polls
instead of 7 and forecasts without them, which is the behaviour the sweep needs.

### A city toml could invent a lever, and one had been doing so since §1.68

`read_scenario_file` has always rejected an unknown key. `apply_city` accepted
anything in `[judgements.scalars]` and wrote it straight into `DEFAULTS`. So
when §1.68 deleted `poll_weight`, `cities/joburg.toml` and `cities/tshwane.toml`
went on carrying it and `apply_city` faithfully put it back — **demonstrated,
not inferred**:

    >>> before = set(M.DEFAULTS); M.apply_city(cityconfig.use("joburg"))
    >>> sorted(set(M.DEFAULTS) - before)
    ['poll_weight']

A key nothing reads, sitting in the model's parameter dict, which
`read_scenario_file` would then *accept* from a scenario file and silently
ignore. That is the half-finished-deletion failure §1.68 caught inside itself,
one layer down and pointing the other way: the sweep guard checks `DEFAULTS`
against `PERTURB`, and this route adds to `DEFAULTS` *after* the guard has
looked. `apply_city` now raises on an unknown scalar, and the two dead lines are
gone.

### The register was making false claims, and the guard could not see them

`test_every_tunable_constant_is_in_the_judgement_register` checks **code →
register**. Nothing checked **register → code**, and that is the direction that
failed:

* **`polling_lean` / `polling_span`** sat in §F marked *"superseded by the poll
  paths; still wired"*. They are not wired. They do not exist. The only trace of
  them in `src/` is the comments recording their deletion. This is the exact
  failure the `poll_half_life_days` row already confesses to — *"this row
  previously named a constant that did not exist"* — repeated.
* **`POLL_RMS_ERROR = 0.030`** is declared live in §F and is read by nothing.
* **`MIN_SHARE` and `F_OTHER`** are filed under `stats.py` / `benchmarks.py`.
  They live in `gamma_recent.py` and `leverage.py`. That row had already been
  corrected once, for `CLAIM_FRACTION`, without checking the other two.
* **Every one of the 24 line citations in §A was wrong**, by 34 to 375 lines,
  several pointing at blank lines — six days after the preamble was rewritten to
  say *"every line number and every claim below was re-checked by running the
  code"*, and directly under its own warning that *"a register that names the
  wrong line is worse than one that names none, because it is checked and
  passes."*

**The line numbers are not corrected; they are removed.** Correcting 24 numbers
fixes 24 instances of a defect that recurs on a timescale of hours and decays
invisibly — this register has now gone stale on line numbers twice in six days.
A name does not drift. Every row cites the module and the symbol, and
`tests/test_register_matches_code.py` enforces both directions:
`test_every_symbol_the_register_names_exists` and
`test_the_register_cites_no_line_numbers`. Deleted levers are listed explicitly
in a `DELETED` map with the entry that removed each, so "this name is not in the
code" is a decision rather than a gap.

Writing that guard immediately found three more register defects nobody had
looked for: `_pr`, `_jitter` and `_noise_sd` — rows abbreviating
`w_bye_local_pr`, `turnout_blend_jitter` and `turnout_noise_sd` into strings
that cannot be grepped. Spelled out.


### What actually changed in the code, in full

Recorded here because §1.69's narrative above is about *why*, and a reader
auditing the diff needs the *what*. Every item is number-neutral unless it says
otherwise, and that was verified at Johannesburg 2016 to every seat and CRPS
figure before anything else was measured.

**Dead instruments removed or wired up** (found by an exhaustive sweep; the
project's own `EXPECTED_INERT` register already covered the levers, so these are
what it does not reach):

| what | where | disposition |
|---|---|---|
| `_rosters` | `montecarlo`, arrivals poll path | **deleted.** Written and never read — the loop seven lines below reads `_roster`, a *different* name bound far above. It re-read an entire VD result file to duplicate work already done, and its `cityconfig.by_code` branch was permanently dead because that function does not exist |
| the bare `except Exception` around the arrivals poll path | `montecarlo` | **narrowed** to `(FileNotFoundError, KeyError, ValueError)`. It wrapped the 48-coherent-seat channel of §1.65, so a `NameError` in there would have disabled all 48 and printed a verbose-only warning — which is precisely how the legacy poll path stayed broken (§1.68) |
| `validate_or_die` inside that same try | `montecarlo` | **lifted out.** §1.68 made a malformed register fatal and then called it from inside a bare except, silently un-fatalling it on that path |
| `pit_all` | `score` | **deleted.** A second full PIT histogram over every scored column, computed on every scoring call and read by nothing. Its sibling `coverage_all` *is* read, which is what made it look deliberate |
| `shapley_p5` / `shapley_p95` | `coalitions` | **now printed.** Two percentile passes over a 5,000-draw array per run, discarded, while the Banzhaf pair was printed. An interval for one power index and a point estimate for the other is not a choice anyone made |
| `cap_undershoots` / `cap_moved` | `montecarlo` | **now printed.** Named in the code as "the counters whose SILENCE was read as success for two days (§1.41)" and still, on 2026-08-22, printed by nothing and asserted on by nothing. They reached the opt-in trace alone, and CLAUDE.md's own warning is that the trace "will happily record a guard that has gone blind" |
| `turnout_limits["pool"]` | `pools` | **documented, not deleted.** Computed and emitted; only `limits["city"]` ever binds. `export_interactive` consumes the emitted block, so the name is corrected in place rather than removed |
| `render_methodology.py`, `build_compare.py` | `src/` | **deleted.** Two orphan renderers, no importer and no reference in any doc. `render_methodology` was superseded by `build_site.render_doc`; this is the `site/plan.html` failure mode CLAUDE.md names, one step earlier in the pipeline |

**Constants promoted from inline literals to named module constants**, resolved
in the function body rather than as default arguments (the §1.33 freezing trap),
so that `test_every_tunable_constant_is_in_the_judgement_register` can see them
at all — it reads module-level assignments and `DEFAULTS`, and none of these was
either:

| constant | value | what it governs |
|---|---|---|
| `ALPHA_MIN_SHARE`, `ALPHA_FLOOR`, `ALPHA_CEILING`, `ALPHA_FALLBACK` | 0.01, 1.0, 200.0, 12.0 | the selection rule feeding `pools.dirichlet_alpha` — §B calls the per-pool concentration the model's **dominant width lever** (83–98% of drawn variance). `dirichlet_scale` multiplies this function's OUTPUT and has been swept for weeks; the four numbers deciding its INPUT were untracked |
| `ARRIVAL_BAND_LO`, `ARRIVAL_BAND_HI` | 0.25, 0.95 | the triangular support of every seeded arrival |
| `BYE_MIN_WEIGHT` | 30.0 | the admission gate on the **whole by-election channel**, sitting beside `w_bye` (registered 🔴) and itself unregistered |
| `TURNOUT_DRAW_FLOOR`, `TURNOUT_DRAW_CEILING` | 0.02, 0.95 | floor and ceiling on per-VD turnout in every draw — note §C describes that band as one that "removes caps rather than adding one" |
| `WARD_PR_RATIO_MIN`, `WARD_PR_RATIO_MAX` | 0.5, 2.0 | the clip on the ward/PR split-ticket ratio, which §E lists as coming *from the record* |

All six are now declared in `JUDGEMENT-CALLS.md` §F at 🔴 and none has ever been
swept.

### The panel was smaller than the archive, for two reasons, and neither was stated

`backtest.runnable_targets` reports what the archive supports: 2011, 2016 and
2021 **for all eight metros — twenty-four city-years.** `compare_history.runnable`
reported nine. Nothing anywhere said why, and the difference had two independent
causes that were indistinguishable from outside because both produced a silent
absence:

* **no emitted pool spec** — mechanical, and needing no new data. Seven metros
  had `pools_2021.json` and nothing else, while the `lge2011_*` and `npe2014_*`
  files a 2016 target reads have been on disk throughout;
* **no γ fold** — a 2016 target needs a γ fold strictly preceding it, which is
  fold 3 (2009 NPE → 2011 LGE), which needs `npe2009` and `lge2006`. **Those
  exist for Johannesburg and for no other metro.**

This matters more than a denominator usually would, because `ITERATING.md`'s
"when to stop" section concluded the model was finished **on the strength of that
number** — nine city-years, eight of them one cycle, therefore ~2 effective
clusters, therefore a panel supporting approximately zero fitted parameters. Part
of that ceiling was an artefact of emission.

**Half of it is now cleared and half of it is not, and the honest report is
both.** All eight 2016 pool specs are emitted (`pools.py --emit`, deterministic;
the artefact key is unchanged because it ignores comments and this pass changed
only comments in `pools.py`). The seven non-Johannesburg 2016 targets are still
blocked, on the γ fold, and there is no way round it: fold 1 targets 2016 itself,
so borrowing its γ reads the answer the backtest is predicting.

So the pre-2011 ingest `ITERATING.md` already names is confirmed as the single
remaining step — and it is now worth **more** than that file estimated, because
the other half of the work is done: the moment `npe2009` and `lge2006` land for
seven metros, seven city-years and a second full electoral cycle arrive with no
further work.

**`compare_history` now prints what it cannot run, and why, on every
invocation:**

```
panel: 9 city-year(s) scored, 15 the archive supports but this harness cannot:
    joburg 2011: no pool spec — run `src/pools.py --city joburg --target 2011 --emit`
    tshwane 2016: no γ fold 3 for this city; it needs the pre-2011 archive, ...
```

Same shape as `polling.screen` (§1.68): a refusal is a returned reason, not a
silent `continue`. The number of city-years is the denominator of every claim
this repository makes and it must not be able to shrink quietly again.

**It also looked like it had found a tenth city-year, and had not.** The report
says `joburg 2011` is blocked only by the missing spec — Johannesburg *does*
have fold 4 (2004 NPE → 2006 LGE), which precedes 2011 — so it read as a free
third electoral cycle. **It is not.** `pools.py --city joburg --target 2011
--emit` fails with *"joburg 2006: no ward joined the census"*: the 2006 ward
geography predates the delimitation the census is joined on, so the pool vectors
cannot be fitted at all. Recorded in the refusal message itself so that nobody
spends a second afternoon on it.

Which is the same lesson as everything else in this entry, one more time: a
report that names ONE blocker will be read as naming THE blocker. The refusal
now says both.

### The published forecast is not the configuration the backtest scores

The headline of this repository is **254 coherent seats against uniform swing's
376**. That is scored on a configuration the live 2026 forecast does not run,
and the difference goes in both directions. It is disclosed in
`EXPECTED_INERT` one lever at a time, which is where a reader will never
assemble it, so it is assembled here.

**Channels live at 2026 that no backtested target can score:** `w_bye` (the
by-election window is 2022-06 to 2026-02); `contestation_expand` (superseded by
real nomination lists wherever a result file exists); and all six poll levers
(the register holds no metro poll of Johannesburg declared for 2021).

**And the magnitude is not small.** Johannesburg 2026, 600 draws,
`poll_paths=off` against `poll_paths=all`:

| party | polls off | polls on | Δ |
|---|---|---|---|
| DA | 65 | **78** | +13 |
| ANC | **68** | 63 | −5 |
| ASA | 31 | 25 | −6 |
| EFF | 25 | 23 | −2 |

**The lead flips.** The ANC is the largest party without the polls and the DA is
the largest party with them. `H_eff` prints as **1.0** — the model knows it has
one effective house — and the DA sits **exactly on the cap**, `w = 0.50`, so the
influence of the poll on the party it moves most is set by `poll_house_k` and not
by the σ arithmetic that `poll_house_k` exists to bound.

This is not a defect. It is a dependence, and the pollster's standing rule is
that you never anchor on a single house because with one house you have a level,
not a house effect. It is now a row in `JUDGEMENT-CALLS.md` §A at 🔴 rather than
something a reader has to reconstruct from the inert-lever list.

### The arrivals poll path could not run at a live target, and a national total was not what was missing

§1.65 measured the arrivals path at **48 coherent seats** — the largest single
effect in the poll channel — and recorded that it was dead at 2026 because
`NATIONAL_VOTES` has no 2026 key. It then asked for one.

**That would not have fixed it.** `contested_share` is a RATIO: votes cast in the
municipalities a party contests, over votes cast nationally. Both halves are
votes cast **at the target election**. `NATIONAL_VOTES["2026"]` supplies the
denominator; the numerator comes from `votes_by_metro("2026")`, which returns
`{}` because no 2026 result file exists and none will until after polling day.
The path was blocked twice and the entry saw one of them.

What is projectable is the ratio itself, and it is measured:

| metro | 2016 | 2021 | change |
|---|---|---|---|
| JHB | 0.0823 | 0.0770 | −6.4% |
| CPT | 0.0818 | 0.0761 | −7.0% |
| ETH | 0.0724 | 0.0646 | −10.8% |
| TSH | 0.0579 | 0.0561 | −3.1% |
| EKU | 0.0589 | 0.0559 | −5.1% |
| NMA | 0.0249 | 0.0220 | −11.8% |
| BUF | 0.0149 | 0.0150 | +0.2% |
| MAN | 0.0156 | 0.0147 | −5.9% |
| **all eight** | **0.4088** | **0.3813** | **−6.7%** |

Every metro fell, which looks like a trend and is what two points always look
like. **n = 2**, so nothing is extrapolated: `polling.PROJECTED_METRO_SHARE`
carries the LAST OBSERVED value and the 2016→2021 movement is quoted as the
uncertainty on it. Declared in `JUDGEMENT-CALLS.md` §F at 🔴, and it fires only
where no backtest can check it — the `contestation_expand` position, stated here
as it is there.

**The backtest is untouched by construction**, and this is checkable rather than
argued: 2016 and 2021 have real result files, so `votes_by_metro` returns real
numbers and the projection is never consulted. At 2021 the projection reproduces
the archive's own answer for JHB+TSH to five decimal places (0.13310 against
0.13308), which is what it should do, since it IS the 2021 value.

**The path still cannot fire at 2026, and the remaining blocker is data.** There
is no national poll declared for 2026 in `polls.json` — the three admitted 2026
records are two SRF metro waves and one metro-aggregate. So the code gap is
closed and the acquisition gap is not:

    admitted at 2026: srf-2026q2-coj (metro), srf-2026q1-coj (metro),
                      ipsos-w2-2025-metros (metro-aggregate)
    national among them: []

**A national poll declared for 2026 is now worth 48 coherent seats of measured
machinery**, and it is the single highest-value item in `SOURCES.md`.

### `entrant_prob`: the derivation is refuted, the typed value stands, and a null has expired

The audit's objection was sound and is worth stating before the measurement that
answers it. `ITERATING.md` says *"the arrival record independently gives
0.29–0.35, and that is the only number worth quoting"*, and the model ships
**0.25** — outside its own stated evidence range, on the low side. §1.31 derived
both ends: matching the arrival record's **median** gives 0.290, matching its
**mean** gives 0.353. It then said that if the constant were ever moved it should
go to *"~0.35 with the arrival record cited"*.

There is a further argument for the mean specifically. Whatever goes into
`centres` IS an expected value, and this repository has made that correction
three times already — flooring the Dirichlet MEAN rather than its concentration,
reporting the coherent seat vector rather than marginal medians, and taking an
arrival's centre as the mean of its comparators rather than their median. On that
principle 0.353 is the derived value and 0.25 is a legacy constant.

**Measured, nine city-years, 1500 draws:**

| city-year | 0.25 | 0.290 | 0.353 |
|---|---|---|---|
| Johannesburg 2016 | 16 | 16 | 16 |
| Johannesburg 2021 | **86** | 88 | 88 |
| Tshwane 2021 | 30 | 30 | 30 |
| Ekurhuleni 2021 | **18** | 20 | 20 |
| eThekwini 2021 | **32** | 34 | 36 |
| Cape Town 2021 | 34 | **32** | **32** |
| Mangaung 2021 | **10** | **10** | 12 |
| Nelson Mandela Bay 2021 | **18** | 20 | **18** |
| Buffalo City 2021 | **10** | 12 | 12 |
| **total coherent** | **254** | 262 | 264 |
| **total CRPS** | **232.7** | 234.3 | 236.1 |

**Both derived values are worse, monotonically, on both scores.** 0.353 costs
**10 coherent seats and 3.4 CRPS**; 0.290 costs 8 and 1.6. *Worse does not ship*
decides it and no further argument is needed: **`entrant_prob` stays at 0.25**,
and `ITERATING.md`'s standing advice to move it to ~0.35 is withdrawn — it was
written before this was measured and it is now refuted.

Note carefully what this is NOT. It is not a constant chosen on the scoreboard,
which rule 10 forbids: 0.25 was not selected because it scores best, it is the
incumbent, and the scoreboard was used to REJECT a proposed change. That is the
one thing the scoreboard is unambiguously for.

**And a null has expired, which is the finding worth keeping.** §1.31 measured
this same constant and concluded *"across 0.25 → 0.40 the seat error moves by 2
in 314 and the CRPS by 2 in 268 — the whole range is inside the noise"*, with the
draw noise itself at ±2 seats. That is no longer true: the same sweep now moves
**10 seats**, five times the noise floor it was compared against. The constant
did not change. The model did — the level shrink (§1.44), the contestation
correction (§1.47) and the poll paths (§1.65) all landed since — and a lever that
was genuinely inert on the old model is live on the new one.

So: **a null is a statement about the model that measured it, and it expires when
that model changes.** This repository already knows that a null measured with a
gate shut is not a null (`_LEGACY_POLL`) and that a null is only as broad as the
output it was measured on (rule 7). This is the third member of that family and
the one nothing guarded against — `EXPECTED_INERT` entries carry a reason but no
date, and nothing re-tests them when the mechanism around them moves.

### The artefact key caught this entry's own author, which is what it is for

Worth recording because it is the one guard in this repository that worked
perfectly, unprompted, against the person who was auditing everything else.

The constant promotions above changed `src/pools.py` — real code, not comments —
so `pools_sha` moved `98ed6eb5dcb92907 → 21a0f7c255997f05` and
`test_every_emitted_pool_spec_carries_a_current_artefact_key` failed with the
right words: *"pools_2026.json is STALE: src/pools.py changed since this spec
was emitted; re-emit before believing any measurement taken against it."*

The order of operations had been wrong. The seven 2016 specs were emitted
BEFORE the promotions, so a canonical measurement had already been taken against
specs the code no longer matched. That measurement had been checked
number-neutral by direct before/after comparison and was in fact correct — but
*"I checked it separately"* is exactly the reasoning the key exists to stop being
sufficient, so all **eighteen** specs were re-emitted and the panel re-measured
from scratch.

Two notes for the next person. Emission is deterministic, so the re-emit changed
nothing but the key — the same result CLAUDE.md already records. And the earlier
check that a comment-only edit does NOT move the hash is also confirmed: an
identical `pools.py` docstring pass earlier in this session left
`98ed6eb5dcb92907` untouched. The hash ignores comments and docstrings, as
documented, and notices everything else.

---

## 1.70 The panel doubles, because the blocker was an ingest bug and not the archive (2026-08-22)

§1.69 reported that seven of the eight metros could not run a 2016 target because
γ fold 3 needs `npe2009` and `lge2006`, and that *"those exist for Johannesburg
and for no other metro"*. **That was wrong, and it was wrong in the way this
repository has been wrong before: a fact about what is on disk in derived form
was stated as a fact about what is available.** The owner asked whether the data
might not already be held. It was.

`SOURCES.md` has recorded since 2026-08-09 that every pre-2011 election is
published as a **single zipped NATIONAL CSV**, and that all six were downloaded,
SHA-256 recorded and archived to `data/raw/elections/_source/`. They cover the
whole country. `src/ingest_historic.py` already advertises `--city`. The seven
metros' files did not exist because **the ingest had never been run for them**,
and — as it turned out — could not have been.

### Running it exposed a silent data-corruption bug

Recorded in full as `DATA-QUALITY.md` item 13; the short form is that
`matches_city` returned on `spec["muni_match"]` **without ever looking at
`city`**, and `npe1999`'s `muni_match` is Johannesburg's two metropolitan local
councils. So `--city tshwane` collected Johannesburg's rows and wrote them to
`npe1999_approx_TSH_vd_party.csv`.

Seven files, **byte-identical to Johannesburg's at 789,426 bytes** — 9,072 rows,
648 VDs, 1,361,299 votes — for metros between 370k and 1.5M votes. **They passed
the reconciliation gate at 648/648 and worst drift 0.00%**, because they were
Johannesburg's real rows and the gate checks that party votes sum to each VD's
valid total, not that the VDs belong to the city on the filename.

This is the third instance of one failure. The `matches_city` docstring already
narrates the Buffalo City case — matching on the last word put 2,087 VDs and 5.1
million votes into a 350-VD metro, *"and it passed the reconciliation gate,
because the rows it collected were individually valid. Only the seat test caught
it."* The fix then was a code-prefix check. It did not cover the `muni_match`
branch, which sits three lines above it and returns first. **A guard written
against one route through a function is not a guard on the function.**

All seven were deleted within the hour and no measurement was ever taken against
them.

### And 2004 matched nothing, which is why this looked like a data gap

`npe2004` has no `muni_match`, fell through to the code/name matcher, found
nothing, and halted — so `lge2006` and `npe2009` were never reached. The
municipality strings are not derivable from a city's name or code: 2004 and 2000
key the Gauteng and Eastern Cape metros on the **place** (`PRETORIA - TSHWANE
METRO`, `EAST RAND - EKURHULENI`, `PORT ELIZABETH - NELSON MANDELA`), and every
archive keys Mangaung and Buffalo City on the **pre-2011 municipality codes**
`FS172` and `EC125`. A table recovers that; no rule does.

`MUNI_HEAD` is that table, enumerated from the archives, matching on the token
before `" - "` so a match cannot spread into a neighbour. **A missing entry is a
refusal, not a fallback** — the fallback is the bug. Two absences are recorded
deliberately: Ekurhuleni and eThekwini in `lge2000`, and every metro but
Johannesburg in `npe1999`.

### Verified before anything was believed

* Johannesburg re-ingests **byte-identically** (md5 unchanged), so no existing
  number moved because of the matcher change.
* **21 files** across seven metros, every one at **100% reconciliation, worst
  drift 0.00%**, with distinct size-plausible totals — Cape Town 1,456,350 votes
  at `lge2006`, Mangaung 301,043, Buffalo City 369,123. Byte-identical totals
  were what exposed the 1999 bug, so distinctness is checked, not assumed.

  > **Six of the 21 — Mangaung's and Buffalo City's — are not on disk as of
  > 2026-08-23, and the numbers below were measured while they were.** See
  > §1.75. Nothing in this entry is withdrawn; it is the tree that moved, and
  > it moved without saying so.
* γ fold 3 fits for all eight metros.
* All **18** pool specs re-emitted afterwards, because the new pre-2011 history
  feeds the θ record and therefore every city-year — not only the new ones.

### The panel

    panel: 16 city-year(s) scored, 8 the archive supports but this harness cannot

**Nine city-years become sixteen, and one effective electoral cycle becomes
two.** The eight refusals are the 2011 targets, and those are genuinely blocked:
`pools.py --target 2011 --emit` fails with *"no ward joined the census"*, because
the 2006 ward geography predates the delimitation the census is joined on. That
is a real limit and it is now in the refusal message.

### What this does to "when is the model done"

`ITERATING.md`'s "when to stop" section concluded that the model was finished,
and the load-bearing argument was the panel: nine city-years, eight of them one
cycle, therefore about two effective clusters, therefore *"this panel supports
approximately zero parameters chosen on it"*. That argument was correct given its
premise. **The premise has changed** — and it was never a fact about South
African electoral data, it was a fact about which ingest had been run.

Two cautions against over-reading this, both of which apply immediately:

* **Sixteen city-years is not sixteen clusters.** They are two cycles of eight
  metros, and metros within a cycle share a national swing. The honest effective
  count is nearer **two cycles** than sixteen observations, which is better than
  ~2 and is not ~30. Rule 10 is not repealed.
* **The 2016 cycle is not a free win.** It is a genuinely independent test of
  every choice made by fitting to 2021, and some of those choices may not
  survive it. That is the point of having it.

Every number in this repository predating this entry was measured on nine
city-years and must be re-read on sixteen before it is quoted again.

### The panel doubled and the model got worse, and that is the result

**16 city-years, 1500 draws, on the settled tree:**

| | model | uniform swing | margin | CRPS |
|---|---|---|---|---|
| **all 16** | **384** | **530** | **27.5%** | 329.4 |
| 2016 cycle (8) | 126 | 180 | 30.0% | 108.5 |
| 2021 cycle (8) | 258 | 350 | 26.3% | 220.9 |

The model beats uniform swing on both cycles, and it beats it by **more** on the
2016 cycle than on the 2021 one. That is the first genuinely out-of-sample
statement this repository has ever been able to make: nothing in the model was
chosen with 2016 metro results in view, because until today they could not be
run.

**And the same change cost 26 coherent seats on the nine city-years that already
existed.** Same city-years, same baselines, same code — the only difference is
that the θ record now contains 2006→2011 transitions for seven more metros:

| city-year | before | after | Δ |
|---|---|---|---|
| Johannesburg 2016 | 16 | 22 | **+6** |
| Johannesburg 2021 | 86 | 90 | +4 |
| Tshwane 2021 | 30 | 34 | +4 |
| Ekurhuleni 2021 | 18 | 22 | +4 |
| eThekwini 2021 | 32 | 36 | +4 |
| Cape Town 2021 | 34 | 36 | +2 |
| Buffalo City 2021 | 10 | 12 | +2 |
| Mangaung 2021 | 10 | 10 | 0 |
| Nelson Mandela Bay 2021 | 18 | 18 | 0 |
| **total** | **254** | **280** | **+26** |

**Not one city-year improved.** Seven got worse and two were unchanged. A
monotone degradation across every affected city-year is not noise — the draw
noise on this measure is ±2 seats (§1.31) and this is +26.

*Worse does not ship*, so this is not adopted on the strength of the bigger
panel. It is written up as a finding and a decision that belongs to the owner,
because the two halves cannot be separated by any means rule 10 permits: the
2016 targets need γ fold 3, fold 3 needs the pre-2011 ingest, and the ingest is
what moves the θ record. Excluding the new metro-years from the θ record *while
keeping them for the fold* would be a choice made on the scoreboard, which is
the one thing the register exists to catch.

**The first hypothesis to test, and it is a data question rather than a
modelling one.** `DATA-QUALITY.md` item 13 already records that Mangaung and
Buffalo City are keyed on `FS172` and `EC125` before 2011 — their
**pre-demarcation municipality codes** — so their 2006→2011 θ ratios mix a
boundary change with a political one. Buffalo City's share of the eight-metro
vote steps 5.1% → 3.9% across exactly that transition, which is the shape a
footprint change makes and not the shape an election makes. Excluding those two
metros' pre-2011 transitions from the θ record is a **data-quality exclusion
with independent justification**, not a fit, so rule 10 permits it — and if it
recovers most of the 26 seats, the cause is the footprint and not the era.

The second hypothesis, if that fails, is exchangeability: 2006→2011 is COPE's
arrival and collapse and the DA's consolidation, and pooling it with 2016→2021
may simply be pooling two different regimes. That would be a real finding about
how far back the θ record should reach, and it would be worth having.

**Until one of those is settled, the committed position is: the ingest bug is
fixed, the data is correct and validated, the panel CAN be sixteen — and the
model that uses all of it scores worse on the nine city-years that could be
checked before today.**

---

## 1.71 A probability of one, and the transition that should never have been pooled (2026-08-22)

Two changes and one measurement, all of them prompted by the owner reading the
ward map and asking why so many wards sat at 100%.

### No ward is published at probability one any more

The map's tooltip read **"DA — DA 100%"** for 25 of Johannesburg's 135 wards on
the 2026 forecast, every one of them DA. The number is P(this party wins the
ward) across draws, not a vote share — but at 1.000 it asserts that P(anyone
else wins) is exactly zero, which is the bounded-support fault: an outcome at
probability zero that then happens carries an infinite log score.

**It is not hypothetical, and it was measured rather than argued.** Backtested
on Johannesburg 2021 at 1500 draws:

| forecast band | wards | right | hit rate | nominal |
|---|---|---|---|---|
| **p = 1.000** | **32** | **31** | **97%** | **100%** |
| 0.99–0.999 | 2 | 2 | 100% | 100% |
| 0.90–0.99 | 15 | 14 | 93% | 94% |
| 0.75–0.90 | 39 | 37 | 95% | 82% |
| 0.60–0.75 | 23 | 17 | 74% | 69% |
| < 0.60 | 24 | 10 | 42% | 48% |

Overall 111 of 135 ward winners called correctly. **Every band except the top
is calibrated or conservative; the top band is the only one that overclaims,
and what it overclaims is certainty.** Ward 7 was PA at p = 1.000 and returned
the ANC.

`p_win` is now the Jeffreys posterior mean `(k + ½)/(N + 1)`, which cannot
reach 0 or 1 from a finite sample: seeing k = N wins in N draws bounds the loss
probability near 1/N, it does not establish zero. At 1500 draws the maximum
publishable probability is **0.9997**. Nothing else moves — the tier counts are
identical (34 at ≥0.99, 49 at ≥0.90) and no seat, median or coherent vector
changes. `tests/test_regressions.py::test_no_ward_is_published_at_probability_one`
fails the build if the raw fraction returns.

**This fixes the ESTIMATOR and not the MODEL.** 97% observed against 99.97%
claimed is still a real over-confidence, and its cause is that the ward draw
carries no mechanism for a local upset — candidate quality, a defection, a
strong independent. `universe` excludes independents outright, which is
defensible for Johannesburg (they won no ward in 2016 or 2021, checked) and is
an assumption everywhere else. That is a modelling change and is not attempted
here.

Worth recording separately: **all 25 certainties were DA and none were ANC.**
The ANC's wards are contested by MK, the EFF, ActionSA and the PA drawing on the
same pools, so rival mass always exists; the DA's strongholds have no comparable
challenger in their pool. The owner read that off the map before it was measured.

### The 2009→2011 transition is three party-structural events, and §1.70's regression is made of it

§1.70 recorded that ingesting the pre-2011 archive for seven metros cost **26
coherent seats** on the original nine city-years, and named two hypotheses. Both
are now settled, and neither was quite right.

**The Mangaung/Buffalo City footprint exclusion recovers 8 of the 26** — a
third. Holding out their pre-2011 files (keyed on the pre-demarcation codes
`FS172` and `EC125`) gives 272 against 280, and 368 against 384 on all sixteen.
Real, worth doing on its own merits, not the main cause.

**The main cause is one transition, and it is not "the old era".** θ dispersion
by transition, parties at or above 5% of the national vote:

| transition | n | sd(log θ) |
|---|---|---|
| 2004→2006 | 15 | 0.226 |
| **2009→2011** | **18** | **0.942** |
| 2014→2016 + 2019→2021 | 46 | 0.200 |

2004→2006 is indistinguishable from the modern era. 2009→2011 is **4.7×** more
dispersed than either neighbour — and it is precisely the transition the seven
metros just added, because γ fold 3 is `npe2009 → lge2011`.

Reading the observations shows why immediately:

| party | θ | what happened between the 2009 NPE and the 2011 LGE |
|---|---|---|
| COPE, six metros | **0.115 – 0.282** | formed December 2008, 7.4% nationally in 2009, collapsed by 2011 |
| IFP | 0.465 | the NFP split away in January 2011 |
| VF+ | 0.420 | — |
| DA, five metros | **1.378 – 1.577** | the Independent Democrats merged into the DA in 2010 |
| ANC, six metros | 0.931 – 1.060 | ordinary retention |

**Excluding the collapses and the merger takes the transition's dispersion from
0.896 to 0.244** — back in line with 0.226 and 0.200. The ANC rows were never
the problem.

So the record does not contain a volatile *era*. It contains a **collapse, a
split and a merger**, being fed into θ as though they were retention — and this
repository already has separate machinery for exactly those events (`SPLITS`,
`splinter_record`, `home_splinter_record`, the arrivals path). Pooling them into
θ double-counts them and inflates the common dispersion for every large party,
which is what widened the top of the ballot and cost the seats.

**This is why a date cutoff is the wrong instrument** and the owner's proposed
"start at 2016" cannot be built anyway: the record for a target must be strictly
before it, so a 2016 floor leaves a 2016 target with **no record at all** and a
2021 target with one transition. (Noted while there: Ramaphosa became ANC
president in December 2017 and State President in February 2018, so 2016 is the
ANC's first metro losses, not his accession.) What the measurement supports is a
**structural-event filter keyed on the tables the model already keeps**, not a
date.

Not implemented here. It changes the θ prior for every city-year and it is a
modelling decision, so it is written up with its measurement and left to the
owner — which is the same disposition §1.70 took and for the same reason.

### And the derived values have not all caught up

The record grew from **n=257 over 18 metro-year clusters** to **n=370 over four
target LGEs**. Two things were re-measured today and moved:

* forward-validated `sd(log θ)` at ≥15% of the vote: **0.138 [0.084, 0.171] →
  0.208 [0.114, 0.299]**;
* `SD_FLOOR = 0.15` binds on **26 of 64** observations there, against 20 of 37
  before, which is why `test_the_floor_binds_at_the_top_of_the_ballot_and_only_there`
  fails. The floor is still inside the new interval; the fit has risen past it.

Three constants carry an `n` in the register that the new archive changes and
have **not** been re-measured:

| constant | measured on | status |
|---|---|---|
| `TURNOUT_CORRELATION` = 0.63 | "14 metro-transitions" | more transitions now exist |
| `SPLINTER_PARENT_WEIGHT` = 0.35 | "22 splinter-metro cases" | more history now exists |
| `SPLIT_SD_FLOOR` = 0.90 | already known to override its own measurement at 2016 | unchanged, still overriding |

None is re-measured here, because re-measuring them against a θ record that is
itself under question would bake in the very transition this entry argues should
be filtered. They are recorded as stale so that nobody quotes their `n` again
without re-deriving it.

---

## 1.72 The swing curve is monotone once you stop pooling two kinds of volatility (2026-08-22)

Proposed by the owner, from first principles and without seeing the code: *"large
parties, more voters, so change less as a percentage. Smaller parties need few
votes to dramatically increase their percentage. I expect there is a 'possible
swing' curve based on size. Now if you do that as an average of all parties,
which are the outliers?"*

That is `sd_for` — a size-dependent dispersion, already fitted and already known
to misbehave. The outlier step is new, and it dissolves a question this log
closed twice.

### The outliers are not a tail. They are a different population.

Standardised against a size-conditional curve, every observation past |z| ≈ 5 is
a named party-lifecycle event:

| party | θ | national share | event |
|---|---|---|---|
| PA, four metros | **10.9 – 100.3** | 0.01–0.09% | growth off a near-zero base |
| AGANG, three | **0.059 – 0.090** | 0.3–0.5% | formed 2013, defunct after 2014 |
| COPE, five | 0.115 – 0.193 | 2.1–9.6% | formed Dec 2008, collapsed by 2011 |
| AIC / NFP | 5.6 – 9.4 | 0.02–0.6% | growth off a tiny base |
| MINORITY_FRONT | 0.193 | 2.4% | founder-leader died 2011 |
| DA, five | 1.378 – 1.577 | 15.8–53.8% | absorbed the Independent Democrats, 2010 |

**Not one is an established party having an unusual election.** Every one is a
formation, a collapse, a merger, a split or a death — and every one was knowable
*before* the election it precedes, which is what makes this usable in a forecast
rather than hindsight.

### The literature already names this split, and names it as the thing not to pool

Powell & Tucker (*BJPS* 2014) decompose the Pedersen volatility index into
**Type A** — volatility from party *entry and exit* — and **Type B** — vote
switching *among existing parties*. Their argument is that the two have
different causes and that pooling them makes the aggregate mean nothing.

This model already agrees in its architecture: θ is a *retention* ratio, which is
Type B, and Type A has its own machinery — `SPLITS`, `splinter_record`,
`home_splinter_record`, the arrivals path, the seeded-arrival bands.
`theta_record` pools them anyway.

### Measured

Same record, n=377, binned as §1.59 bins it. Removing the 79 Type A observations
(21%):

| size band | pooled — what the model uses | Type B only |
|---|---|---|
| <0.2% | 0.860 | **0.573** |
| 0.2–1% | 0.722 | **0.512** |
| 1–5% | 0.511 | **0.395** |
| **5–15%** | **0.817** | **0.221** |
| ≥15% | 0.282 | **0.211** |

**The curve becomes monotone decreasing in size** — which is the owner's
prediction, arrived at from the arithmetic of "a small party needs few votes to
double" and confirmed on the record.

**And the 5–15% anomaly disappears: 0.817 → 0.221.** That anomaly is not a minor
detail of this log. §1.59 measured it and concluded the *functional form* of
`sd_for` was wrong — *"the forward-validated conditional dispersion is not
monotone in size, and a straight line cannot be right in the middle and at both
ends"*. §1.62 then built two refits against it, lost both folds, and closed the
question: *"No further functional form may be tried against these two folds."*

**The 5–15% anomaly those entries could not fit is COPE's collapse in four
metros of one transition, and no straight line was going to fit that.** That is
the defensible statement and it is worth having on its own.

> **AMENDED THE SAME DAY, BEFORE ANYONE ACTED ON IT.** This paragraph first read
> *"The form was never the problem. The population was a mixture."* An
> independent review put three placebo tests against it and that sentence does
> not survive them.
>
> * **The result is not a generic consequence of dropping 21% of the data.**
>   Removing 5 observations *at random* from the 5–15% bin, 2,000 times, gives a
>   median sd of **0.828**, a 5th percentile of 0.658 and a minimum of 0.288.
>   Type A removal gives **0.221 — below the minimum of 2,000 random draws.**
>   That objection is dead and the finding is real.
> * **But the Type A LABEL is doing almost no statistical work.** Dropping the
>   five most extreme `|log θ|` observations *regardless of cause* gives
>   **0.273**, against Type A's 0.221. Nearly all of the fall from 0.817 is
>   "remove the five biggest outliers", which is selection on the dependent
>   variable. **On this evidence the principled rule and the unprincipled one
>   cannot be told apart.** What Type A adds is *interpretation*, not
>   identification — and the real case for it is that **the rule is knowable
>   before the election and outlier-dropping is not**, which is a stronger claim
>   and is completely untested.
> * **The bin that carries the claim is one party.** After removal the 5–15%
>   bin is `EFF 11 · IFP 2 · DA 1 · ID 1 · MINORITY_FRONT 1 · VFPLUS 1`. Eleven
>   of seventeen are the EFF, sharing a party, a leader, a cycle and a national
>   swing, so the effective n is **4–6, not 17** — and `ITERATING.md` rule 11
>   applies to this bin exactly as it applies to the scoreboard. Symmetrically,
>   the five removed are four COPE observations and one IFP, **all from a single
>   transition**.
>
> So "0.817 → 0.221" is, stated honestly, *one party's collapse observed in four
> metros of one transition*. Everything this entry needs follows from the
> amended sentence above; the stronger one is the sentence a reviewer would go
> after first, and it was written before the placebo was run.

### What follows, and the trap in it

This also explains §1.70. The pre-2011 ingest cost 26 coherent seats because γ
fold 3 is `npe2009 → lge2011`, and that transition is **made of Type A events** —
COPE forming and collapsing, the ID merging into the DA, the NFP splitting from
the IFP. Seven metros' worth of them entered the retention prior at once. The
fix is therefore **not** the date cutoff of §1.71, and not the Mangaung/Buffalo
City exclusion that recovered 8 of the 26: it is to route Type A out of θ and
keep all sixteen city-years.

**The trap, stated before anyone implements this.** Removing Type A from θ must
NOT mean the model stops forecasting Type A. Those events are the model's worst
failures — ActionSA is 90 of the 384 — and a retention prior cleaned of every
collapse and surge is a prior that says collapses and surges do not happen. The
change is **route them, not drop them**: Type A observations belong to the
arrivals and splinter machinery, which already exists and is already scored (the
arrivals poll path at 48 coherent seats, §1.65). Delete without routing and the
model gets narrower, more confident, and wrong in exactly the direction it is
already wrong.

Note also that the PA's four observations are Type A *growth* — the same
phenomenon as ActionSA's arrival — and the PA is currently forecast at 19
Johannesburg seats for 2026. Whatever handles Type A has to carry that.

### Not implemented

`theta_record` is unchanged. This is a diagnostic measurement, the change moves
the θ prior for every city-year, and the Type A table above is hand-built from
named events rather than derived from `SPLITS` — which is where it would have to
come from before it could ship. Recorded so the next person starts from the
population question rather than from another functional form.

---

## 1.73 How to tell the two volatilities apart, and what transfers from abroad (2026-08-22)

Two questions from the owner on §1.72: *how do we disentangle the two mechanisms
per Powell & Tucker?* and *big events' impact is a judgement call but an essential
one — find historical impacts for founder death, splitting, joining; need not be
South African, the impact should hold across parties.*

### You do not infer the split from the numbers. You look it up.

This is the part that makes §1.72 usable rather than circular. Powell & Tucker's
contribution is **coding rules**, not a statistical decomposition: a party-year
is Type A because a documented formation, merger, split or dissolution happened,
which is a fact about the party register and the newspapers, not about the vote.

§1.72 *found* its outliers by z-score, which would be circular on its own — every
large residual is an outlier by construction. What makes them real is that each
one then **survives a lookup**: COPE formed December 2008 and collapsed by 2011;
the Independent Democrats merged into the DA in 2010; the NFP split from the IFP
in January 2011; Agang was formed in 2013 and defunct after 2014; the Minority
Front's founder died in 2011. Dates, names, causes — none of it read off a result
file, all of it knowable **before** the election it precedes, which is the only
thing that makes it usable in a forecast.

So the classifier is a table, and the z-scores are how the table gets audited.

**Where it is genuinely ambiguous, and these must be declared rather than
resolved:**

* **Both at once.** A party can decline for ordinary unpopularity *and* lose its
  leader. Nothing in the votes separates the two.
* **COPE 2009→2011 is the hard case in this record.** Was the collapse Type A —
  a party failing as an institution — or Type B, voters returning to the ANC?
  Defensibly both. Powell & Tucker can code it because they work on where the
  *votes* went, at system level; a per-party retention ratio cannot see that.
* **Identity across elections.** "Is this the same party?" is Powell & Tucker's
  own hardest coding problem, and renames, successor parties and electoral
  alliances all sit in it.

The honest structure is therefore **three-way, not two-way**: clean Type B ·
known Type A · ambiguous — with ambiguous handled by **widening** rather than by
exclusion, because an ambiguous case excluded is a case decided.

### What the cross-national record actually says, class by class

The owner's expectation was that these impacts hold across parties and need not
be South African. That is right for two of the three classes and **wrong, with
the sign reversed, for the one that looked most obvious.**

**Founder or leader DEATH — DOES NOT TRANSFER, and the naive import would be
backwards.** The comparative finding is a *sympathy vote*: Berlinguer's death in
Italy in 1984 raised the PCI's share in that election and in later ones, and
Abe's assassination in 2022 is estimated to have given the LDP about six per cent
more seats. This model's own observation runs the other way — the Minority Front
at **θ = 0.193** after Amichand Rajbansi died in 2011.

Both are right, and the moderator is **institutionalisation**. A death helps a
party that outlives its leader and destroys one that *is* its leader. That
distinction is decisive here, because almost every party this model must handle
is a personal vehicle: MK is Zuma, ActionSA is Mashaba, GOOD is De Lille, the EFF
is Malema, Agang was Ramphele, the Minority Front was Rajbansi, the PA is
McKenzie, COPE was Lekota and Shilowa. **Importing the sympathy-vote prior would
have been actively harmful**, and it is exactly the sort of thing that looks
well-sourced in a footnote.

Leadership *change* short of death transfers better: parties with new leaders
lose about 3.5% of their vote on average.

**SPLITS — transfers, and is better than what this model uses.** The largest
study covers **more than 200 splits across 25 European countries** post-war, and
finds the first-election vote shares of both the rump and the splinter predicted
by **membership strength and the share of legislators who defected**. Both are
knowable before polling day. This model currently uses `SPLINTER_PARENT_WEIGHT =
0.35` — a flat fraction of the parent, identical for every split — where the
literature says the defecting-legislator share is the covariate. That is a
concrete, ex-ante-observable improvement over a typed constant, and it is
registered at 🔴.

**MERGERS — thinnest of the three.** The literature is mostly about *why* parties
merge (clearing thresholds, contesting for the largest-party position) rather
than what the merged vote comes to. The model has no merger machinery at all, and
the Independent Democrats merging into the DA in 2010 is sitting in the θ record
as five observations of the DA "retaining" 1.38–1.58 of itself.

### What this changes

`SPLITS` covers **births** — a named person leaving a named party — and it is
good. It has no representation of a party's **death**, a **merger**, or **what a
split costs the parent**, and those are where §1.72's outliers actually live. The
gap is precise and it is the next thing to build.

Nothing implemented. Recorded so that whoever builds the event table starts from
a three-way classification, uses the defecting-legislator share for splits, and
does **not** import the sympathy-vote finding for deaths without the
institutionalisation moderator attached to it.

### Sources

Recorded in full because this entry imports evidence from outside the project
for the first time, and an unsourced claim about another country's elections is
worse than no claim. Also filed in `SOURCES.md`.

**The Type A / Type B decomposition**
* Powell, E. N. & Tucker, J. A. (2014), "Revisiting Electoral Volatility in
  Post-Communist Countries: New Data, New Results and New Approaches",
  *British Journal of Political Science* 44(1).
  <http://www.eleanorneffpowell.com/uploads/8/3/9/3/8393347/powell_tucker_2014_bjps.pdf>
  — the decomposition itself and, more usefully here, the **coding rules**.
* "Rethinking Electoral Volatility", Good Authority.
  <https://goodauthority.org/news/rethinking-electoral-volatility/>
  — plain-language account of the Pedersen index and what the A/B split is for.

**Party splits — the class that transfers, and beats `SPLINTER_PARENT_WEIGHT`**
* "Electoral Competition after Party Splits", *Political Science Research and
  Methods*. <https://eprints.soton.ac.uk/407531/1/splits_el_conseq.pdf>
  — 200+ splits across 25 European countries post-war. Rump and splinter
  first-election shares predicted by **membership strength and the share of
  legislators who defected**, both observable before polling day.

**Leader death — the class that DOES NOT transfer, sign reversed**
* "Berlinguer, I Love You (Still): The Downstream Effects of Expressive Voting",
  *Political Behavior* (2025).
  <https://link.springer.com/article/10.1007/s11109-025-10095-7>
  — the PCI gained after Berlinguer's death in 1984, in that election and later.
* "The Effects of Political Martyrdom on Election Results: The Assassination of
  Abe". <https://arxiv.org/pdf/2305.18004>
  — the LDP estimated ~6% more seats.
* So, MF at θ = 0.193 after Rajbansi died in 2011 is not a contradiction of these
  — it is the personal-vehicle case, and the institutionalisation moderator is
  the whole content of the finding.

**Leadership change short of death**
* So, F., "The Consequences of Party Leadership Change on Democratic Elections".
  <http://www.scpi.politicaldata.org/SCPII/Florence%20So.pdf>
  — parties with new leaders lose about 3.5% of their vote on average.

**The size-dependence question, for context**
* "Simulating Party Shares", *Political Analysis*.
  <https://www.cambridge.org/core/journals/political-analysis/article/simulating-party-shares/C391F0D44529EE6E73F904F2D1E1050F>
  — uniform against proportional swing. θ is a ratio, so this model sits at the
  proportional end; `benchmarks.uniform_swing` is the additive one; the owner's
  "big parties move less than proportionally" is the contested middle.

---

## 1.74 The Type A register, pre-registered (2026-08-22)

**Written and committed BEFORE the measurement, which is the whole point.** §1.72
built its Type A list partly by looking at which observations had large
residuals, and an independent review showed why that will not do: dropping the
five most extreme `|log θ|` observations *regardless of cause* gives sd = 0.273
against Type A's 0.221, so on that evidence **the principled rule and plain
outlier-dropping cannot be told apart**. The register below is built from
documented party events only. No residual was consulted in writing it.

### The rule

Powell & Tucker's Type A is volatility from party **entry and exit**. Most of it
never reaches `theta_record` at all, because that function requires
`before[party] > 0` and `party in set(before) & set(after)` — a party that did
not contest the base election, or does not contest the target, is already
excluded. **Three kinds of Type A survive that filter**, and they are the whole
register:

1. **`MERGER_ABSORBED`** — the surviving party's vote at the target includes a
   party that no longer exists, so its ratio is inflated by an acquisition
   rather than by retention.
2. **`SPLIT_PARENT`** — a party that lost a faction *between* the base and the
   target, so its ratio is depressed by a departure rather than by persuasion.
   The *child* is already excluded (no base vote); only the parent survives.
3. **`POST_FORMATION_COLLAPSE`** — a party that contested both elections but
   whose base reading was a founding surge, so the ratio measures a failure to
   institutionalise rather than a swing.

A fourth, `LEADER_DEATH`, is included where the party is a personal vehicle,
because §1.73 establishes that the effect flips sign with institutionalisation
and is therefore not retention either.

### The register

Every row carries a date and a public event. Nothing here is inferred from a
vote.

| target LGE | party | event | evidence |
|---|---|---|---|
| 2011 | `DA` | `MERGER_ABSORBED` | the Independent Democrats merged into the DA — announced 15 August 2010, completed before the May 2011 LGE. The DA's 2011 vote contains the ID's; its 2009 base does not |
| 2011 | `IFP` | `SPLIT_PARENT` | the National Freedom Party, founded by Zanele Magwaza-Msibi, the IFP's National Chairperson, in January 2011 — four months before the LGE. Already in `pools.SPLITS` as `NFP → IFP` |
| 2011 | `COPE` | `POST_FORMATION_COLLAPSE` | formed December 2008, contested the April 2009 NPE at 7.4% nationally as a founding surge, and had fractured into rival leadership factions by 2011 |
| 2016 | `AGANG` | `POST_FORMATION_COLLAPSE` | Agang SA, founded by Mamphela Ramphele February 2013, contested the 2014 NPE, effectively defunct thereafter |
| 2016 | `MINORITY_FRONT` | `LEADER_DEATH` | Amichand Rajbansi, founder and sole national figure, died 29 December 2011 — after the 2011 LGE and before 2016. A personal vehicle by §1.73's test |
| 2021 | `DA` | `SPLIT_PARENT` | Herman Mashaba, the DA's own mayor of Johannesburg, resigned the party October 2019 and founded ActionSA in 2020, between the 2019 NPE base and the 2021 LGE. Already in `pools.SPLITS` as `ASA → DA` |

**Two deliberate exclusions, stated so they are decisions rather than
oversights.**

* **The PA is NOT in the register**, although it supplies the four largest
  residuals in the record (θ from 10.9 to 100.3). By Powell & Tucker's rule it is
  Type B: it existed at both elections and merely grew. Its extreme ratios are a
  *small-denominator* problem — a party on 0.03% of the vote — and this model
  already handles that with `_reliability(share)` weighting rather than by
  exclusion. **Including it would be exactly the residual-driven choice this
  entry exists to avoid**, and it is the clearest test of whether the register
  was built honestly.
* **The EFF is NOT in the register.** It was founded in 2013 and contested the
  2014 NPE, so by the 2014→2016 transition it exists at both ends and its growth
  is ordinary Type B. It supplies eleven of the seventeen observations in the
  5–15% bin, so excluding it would empty the bin that carries §1.72's headline —
  which is a reason to be careful, not a reason to exclude it.

### The pass condition, fixed in advance

The change ships **only if both** of the following hold. Either alone is
insufficient, and a result that meets neither is a refutation of §1.72's
magnitude, not of its mechanism.

1. **Held-out NLL improves on the committed model in BOTH the 2016 and 2021
   folds** of the §1.61 protocol. This is the bar §1.62's two refits already
   failed, and it is the bar because a form that wins one fold and loses the
   other is what §1.61 defines as undetermined.
2. **Coherent seat error on the sixteen city-years falls below the pre-ingest
   254**, measured at 1500 draws on a settled tree.

Declared in advance, per the review that set these terms:

* **Improvement in the 5–15% bin alone does not count.** That bin is eleven-
  seventeenths EFF, sharing a party, a leader, a cycle and a national swing, so
  its effective n is four to six and `ITERATING.md` rule 11 applies to it exactly
  as it applies to the scoreboard.
* **The sixteen city-years are not sixteen clusters.** They are two cycles of
  eight metros, and any reported improvement must be read at two effective
  clusters, not sixteen.
* **The blunt comparison is already on record and does not count as a pass.**
  Dropping the *entire* 2009→2011 transition — `THETA_EXCLUDE_TARGETS=2011` —
  gives 256 on the original nine against 280, and 32.9% margin against 27.4% on
  the fourteen city-years that keep a baseline. That is what the mechanism is
  worth when applied with a blunt instrument, and it also **destroys the
  uniform-swing baseline for Mangaung and Buffalo City 2016**, because the
  benchmark needs the transition the flag removes. The targeted filter must beat
  the pre-ingest 254 on its own terms, not merely reproduce the blunt result.

### The result: REFUTED against its own pre-registered bar

Both tests were run with the register exactly as committed above. Neither
condition is met.

**Condition 1 — held-out NLL must improve in BOTH folds. It does not.**

| target | n | committed (filter off) | Type A filter on | |
|---|---|---|---|---|
| 2006 | 66 | −0.5499 | −0.5499 | unchanged |
| 2011 | 69 | 5.7630 | 5.7630 | unchanged |
| **2016** | 97 | **0.8900** | **1.0339** | **worse** |
| **2021** | 138 | **0.2603** | **0.0322** | better |

Wins one fold, loses the other — which is precisely what §1.61 defines as
**undetermined**, and it is the same verdict §1.62's two refits received. The bar
was set at both folds for exactly this reason and it was set before the run.

**Condition 2 — seat error on the sixteen must fall below the pre-ingest 254.
It does not.**

| city-year | pre-ingest | full ingest | **Type A** | blunt drop-2011 |
|---|---|---|---|---|
| Johannesburg 2016 | 16 | 22 | **14** | 12 |
| Johannesburg 2021 | 86 | 90 | 88 | 88 |
| Tshwane 2021 | 30 | 34 | **30** | 26 |
| Ekurhuleni 2021 | 18 | 22 | 22 | 20 |
| eThekwini 2021 | 32 | 36 | 36 | 36 |
| Cape Town 2021 | 34 | 36 | **34** | 36 |
| Mangaung 2021 | 10 | 10 | **10** | 8 |
| Nelson Mandela Bay 2021 | 18 | 18 | **16** | 18 |
| Buffalo City 2021 | 10 | 12 | **10** | 12 |
| **original nine** | **254** | **280** | **260** | **256** |
| **all sixteen** | — | 384 | **352** | 354 |
| CRPS, all sixteen | — | 329.4 | **318.1** | 318.1 |

**A flaw in the pre-registration, stated rather than exploited.** Condition 2 as
written compares a sixteen-city-year total against a nine-city-year one, which
is not like-for-like and is my error. On the comparable subset the answer is the
same and there is nothing to argue about: **260 against 254.** The filter
recovers 20 of the 26 seats and does not reach the bar.

**And it does not beat the blunt instrument it was built to improve on.** The
pre-registration said in advance that reproducing the whole-transition drop
would not count as a pass. The targeted filter does not even reach it — 260
against 256 on the nine, 352 against 354 on the sixteen, identical CRPS.

### What was learned, which is more than the verdict

**The mechanism is confirmed and the register is not the way to use it.** Both
interventions recover most of the regression, from opposite directions, so
2009→2011 is beyond doubt the source of §1.70's 26 seats. What fails is the
specific claim that a documented-event exclusion is the right correction.

**The reason is visible in the dispersion table, and §1.72 predicted it in
writing.** With the filter on, `sd_for` at 5–15% falls **0.203 → 0.150** while
the measured conditional dispersion stays at **0.839** — so the ratio worsens
from 4.24× to 5.58×, and the cluster CI excludes the model's value by more than
it did before. Cleaning the fitting record made the model **narrower**, while the
evaluation record still contains the events, because the events really happened.

That is the trap §1.72 named before this was run: *"Removing Type A from θ must
NOT mean the model stops forecasting Type A… Delete without routing and the
model gets narrower, more confident, and wrong in exactly the direction it is
already wrong."* It is satisfying to have written that down first and it is the
reason the entry does not now need re-interpreting.

**So the finding stands and the remedy does not.** Route, do not drop — and this
result says the routing has to be built before any exclusion is worth trying
again. An exclusion on its own transfers the volatility from the model's prior
into the model's error, and the seat count is where it lands.

### Disposition

* `levels.TYPE_A_EVENTS` and `levels.FILTER_TYPE_A` stay in the tree,
  **off by default**, because the register is a documented artefact worth
  keeping and the flag is how the next attempt gets measured. Neither is
  promoted to a `DEFAULTS` lever; §1.74's own terms said promotion required the
  pass, and there was no pass.
* `levels.THETA_EXCLUDE_TARGETS` likewise stays as an experiment harness.
* **The 26-seat regression of §1.70 remains open**, and the tree still carries
  it: 280 against 254 on the original nine with everything at its default. Under
  *worse does not ship*, that is unchanged by this entry.

---

---

## 1.75 Six verified input files left the record between the measurement and the commit, and nothing said so (2026-08-23)

**Not the finding this was looking for.** Task P2c set out to test §1.70's
footprint hypothesis — that Mangaung and Buffalo City's pre-2011 θ ratios are
contaminated by the 2011 demarcation and that excluding them recovers the 26
coherent seats the panel doubling cost. The first step was to establish that the
hypothesis was testable. It is, and establishing that turned up something worse.

### The record and the archive disagree, and only one of them is checked

Counted out of `levels.theta_record` and `levels.local_record` themselves, per
metro, at target 2021:

| metro | θ pre-2011 | θ 2011+ | ρ pre-2011 | ρ 2011+ |
|---|---|---|---|---|
| JHB | 18 | 24 | 20 | 13 |
| CPT | 13 | 33 | 12 | 17 |
| ETH | 12 | 22 | 9 | 11 |
| TSH | 11 | 26 | 11 | 13 |
| EKU | 10 | 23 | 12 | 10 |
| NMA | 9 | 20 | 8 | 10 |
| **MAN** | **0** | 9 | **0** | 9 |
| **BUF** | **0** | 9 | **0** | 8 |

**Mangaung and Buffalo City contribute nothing before 2011.** The six files they
would come from — `npe2004`, `lge2006`, `npe2009` for each — are not in
`data/raw/elections/`, and `find` returns no copy of them anywhere under
`data/raw/`.

The obvious reading is that the ingest never ran for those two. It is wrong.
`MUNI_HEAD` carries `FS172` and `EC125` for all three archives, and running
`ingest_historic` for both metros today succeeds on every one:

| | rows | VDs | reconciliation | votes |
|---|---|---|---|---|
| MAN `npe2004` | 2,639 | 203 | 203/203, drift 0.00% | 269,783 |
| MAN `lge2006` | 4,041 | 231 | 462/462, drift 0.00% | **301,043** |
| MAN `npe2009` | 3,346 | 239 | 239/239, drift 0.00% | 288,332 |
| BUF `npe2004` | 3,354 | 258 | 258/258, drift 0.00% | 291,804 |
| BUF `lge2006` | 4,009 | 298 | 593/593, drift 0.00% | **369,123** |
| BUF `npe2009` | 5,134 | 302 | 302/302, drift 0.00% | 308,336 |

301,043 and 369,123 are **the exact figures §1.70 quotes** in its verification
bullet, alongside its count of *"21 files across seven metros"*. Fifteen files
across five metros are on disk. So §1.70's verification did run for all seven,
these six files existed when it was written, and they are gone now.

### They were still there when the derived artefacts were built

The timestamps settle the order, and they rule out the possibility that §1.70
verified files it never wrote:

| | time (22 Aug) |
|---|---|
| pre-2011 ingest, JHB → TSH → EKU → ETH → CPT | 08:56:53 – 08:58:24 |
| a 29-second gap where **mangaung** runs in config order | 08:58:24 – 08:58:53 |
| NMA, then nothing further | 08:58:53 – 08:59:04 |
| `data/processed/mangaung/fold3_parameters.csv` | **09:00:27** |
| `data/processed/buffalocity/fold3_parameters.csv` | **09:00:31** |
| pool specs for MAN, BUF at 2016 and 2021 | 09:22 – 09:27 |
| `history.json` — the panel measurement | 09:43:13 |
| §1.70 committed (`933183c`) | 15:04 |

**γ fold 3 is the 2009 NPE → 2011 LGE fold.** It cannot be fitted for Mangaung
without `npe2009_MAN` and `lge2006_MAN`, and it was fitted at 09:00:27. Those two
fold files are still on disk, still read by every 2016 target, and are **derived
from inputs that no longer exist.**

So the sequence is: the files were ingested, γ fold 3 was fitted from them, the
pool specs were emitted with them present, **the panel was measured with them
present**, and at some point before this session they were removed without a
line anywhere recording it.

### Which means the current tree does not reproduce the committed numbers

§1.70's headline — 384 coherent on sixteen city-years, CRPS 329.4, and the +26 on
the original nine — was measured against a θ record containing Mangaung's and
Buffalo City's 2004→2006 and 2009→2011 transitions. **The tree at HEAD does not
contain them.** Nothing announces the difference:

* `_citywide` catches `FileNotFoundError` and returns `{}`. Its own comment says
  why that is dangerous — *"A swallowed file error is indistinguishable from a
  deliberate exclusion, which is why it survived. See MODEL-LOG §1.43."* §1.43
  fixed the one template that was then wrong. **The mechanism was left in place,
  and it has now silently eaten twelve transitions instead of one.**
* The `artefact_key` guard hashes `config/dimensions.toml` and `pools.py`'s code.
  It does not hash the election archive, so a pool spec built from six files that
  have since vanished reports itself current, correctly, and uselessly.
* No test asserts that every (metro, transition) the CALENDAR names either has
  its file or is on a declared exclusion list. That is the guard this class of
  failure needs and there is not one.

### What it does to §1.70's open question

**Hypothesis 1 is not refuted — it is untested, and it is now the only way to
read the tree.** The current state *is* the exclusion §1.70 proposed, applied by
accident rather than by rule and applied to the raw files rather than to the
transitions. That makes the next measurement worth taking and worth taking
carefully, because three states are in play and only one of them has ever been
scored:

| state | θ record | γ fold 3 for MAN/BUF | scored |
|---|---|---|---|
| A — as §1.70 measured | MAN/BUF pre-2011 **in** | fitted from present files | **384 / 280** |
| B — HEAD today | MAN/BUF pre-2011 **out** | fitted from **absent** files | never |
| C — the exclusion done properly | MAN/BUF pre-2011 transitions excluded by a declared rule | refitted consistently | never |

State B is not a hypothesis anybody chose. It is state A with six inputs
missing and their derived artefacts left behind, which is the worst of the three
because it looks exactly like the other two from the outside.

### Restored, and the committed numbers reproduce exactly

The ingest is deterministic, so state A was rebuilt rather than reconstructed:
re-ingest the six files, refit γ fold 3 for both metros, re-emit all eighteen
specs, re-measure at 1500 draws.

**The refitted fold-3 artefacts are byte-identical to the ones fitted on 22 Aug
at 09:00** — md5 `f1945ed…` for Mangaung and `faef6d7…` for Buffalo City, matched
against the files that had been sitting on disk derived from inputs that were
not. That is the proof that the restored files ARE the deleted ones, and not
merely files that look like them.

The panel then reproduces the committed scoreboard **exactly**: 384 coherent
across sixteen city-years, 280 across §1.70's original nine, CRPS 329.4, and
**no per-city-year difference at all**. §1.70's numbers are sound; the tree that
produced them is back.

### And state B was worth measuring on the way past

Because the accidental exclusion is, in crude form, the very thing §1.70
proposed. Measured at 1500 draws before the restore:

| | 16 city-years | §1.70's nine | CRPS |
|---|---|---|---|
| **A** — MAN/BUF pre-2011 present (committed) | **384** | **280** | 329.4 |
| **B** — the six files absent (HEAD as found) | **368** | **272** | 329.0 |

**Sixteen coherent seats better, and monotone** — Johannesburg 2016 and 2021,
Tshwane 2021, eThekwini 2016, Cape Town 2021, Nelson Mandela Bay 2016 and
Buffalo City 2016 improve; nine city-years are unchanged; **none is worse**.
CRPS is flat, which is what a change in the θ centre and not in the widths looks
like. Draw noise on this measure is ±2 (§1.31), so 16 is not noise.

**This is not the hypothesis passing its test, and it must not be reported as
one.** Three reasons, all disqualifying on their own:

* **It was not pre-registered.** It was found while checking whether a committed
  number still reproduced. §1.61's discipline exists precisely so that a result
  discovered this way is not then dressed up as a prediction, and §1.74's Type A
  refutation is trustworthy only because that rule was kept.
* **It over-excludes.** Deleting the raw files removes Mangaung's and Buffalo
  City's **2004→2006** transition too, and that one crosses no demarcation — both
  its endpoints are pre-2011. The footprint argument does not reach it. It also
  strips both metros out of the ρ record, which §1.70's hypothesis never
  mentioned.
* **It is internally inconsistent.** γ fold 3 for both metros stayed on disk,
  fitted from the very files the state removes. No configuration anyone would
  choose looks like that.

So the honest statement is narrow and it is still worth having: **the θ record's
pre-2011 Mangaung and Buffalo City observations cost this panel 16 coherent
seats, and removing them harms nothing.** That is a strong prior in favour of
§1.70's hypothesis 1 and it is not a measurement of it.

### Two more guards that were quietly not running, found on the way

Neither is the subject of this entry and both are the same shape as it — a thing
that looks like it is being checked and is not.

**1. Four test files could not be run the way `CLAUDE.md` documents.**
`tests/_support.run_module` takes a namespace dict; `run_all.py` calls it as
`run_module(vars(module))`. `test_levels_dispersion`, `test_polling_sd`,
`test_polling_synthetic` and `test_polling_register` all end with
`run_module(sys.modules[__name__])` — a module, not a dict — so running any of
them directly died on `AttributeError: module '__main__' has no attribute
'items'` **before a single test executed**. Under the suite they passed, because
the suite supplies the dict. All four are files this project added in the last
week. `run_module` now accepts either.

**2. Five test files hid nine tests from their own standalone invocation.**
A file's `if __name__ == "__main__":` block runs at the point it appears, so a
test defined below it is never collected when the file is run directly.
`test_temporal` collected **4 of 8** — including, before this session added
them, the two poll-path guards. `test_calibration_report` hid two,
`test_levers_are_live`, `test_pool_bounds` and `test_regressions` one each.
Every one of them passed under the suite and printed a complete-looking pass
count standalone. The blocks are moved to the end of each file and
`test_no_test_file_defines_a_test_after_its_main_block` now fails if it happens
again.

Neither hid a real failure — checked by running all of them. The point is that
neither COULD have shown one, and the reason both survived is the reason the six
files survived: the thing that would have complained was the thing that was
broken.

### Disposition

* **The tree is restored and no committed number moves.** State A is the tree
  again, verified to the seat.
* **The hypothesis is now testable as state C** — the demarcation-crossing
  transitions only, excluded by a declared and settable rule, with fold 3 refit
  consistently — and its pre-registration must say **in advance and in writing
  that the direction is already known**, because it is. A bar set after seeing
  16 seats is not the same instrument as one set blind, and pretending otherwise
  would be worth less than admitting it.
* **The guard is the part that generalises.** A missing election file must be a
  named refusal, the way a missing `MUNI_HEAD` entry already is. §1.43 wrote that
  lesson and fixed one instance of it; this is the second, and this time it cost
  a headline number's reproducibility for a day without anything going red.

---

## 1.76 `poll_min_n` was filed as inert at 2021 on a reason that was never true of it (2026-08-23)

Found by the suite, on the baseline run that §1.75's work required before
anything could be changed. `test_every_tunable_lever_actually_moves_the_forecast`
failed with the message the register is built to produce:

    poll_min_n IS live at 2021 but EXPECTED_INERT claims it is not

**The register was wrong, and it was wrong because one reason string was reused
for six levers when it was only true of five.** §1.69 added `_NO_METRO_POLL` —
*"the metro-poll path is the only consumer of this lever and the register holds
no metro poll of Johannesburg declared for 2021"* — and attached it to
`poll_house_k`, `poll_deff_subsample`, `poll_screen_sd`,
`poll_drift_per_root_day`, `poll_half_life_days` **and `poll_min_n`**. For the
first five it is exactly right: each is read only where σ_poll is priced for a
metro poll, and there is no such poll at 2021.

`poll_min_n` is not one of those. The floor is applied in `polling.screen`
**before every scope test**, so it is not a metro-path lever at all:

    floor = float(min_n if min_n is not None else POLL_MIN_N)
    for poll in ...:
        if poll.get("numbers") and n is not None and float(n) < floor:
            ...decline...          # <- runs for national polls too

and the arrivals path calls the same function:

    _usable = [q for q in _polling.screen(target, min_n=_min_n)[0]
               if q.get("scope") == "national"]

The sweep perturbs the floor to 5,000. `ipsos-2021-lge-national` has n=1,501, so
at 5,000 it is declined, the arrivals path loses the only poll it has, and the
2021 forecast moves. The lever is live at 2021 — through the arrivals path, not
the metro path. The same is true at 2016, where the national poll is n=3,142.

### Why it survived §1.69

§1.69 is the entry that MOVED the floor from `validate` to `screen`, for good
reasons recorded there: as a fatal validation rule it killed the whole run the
moment the floor was swept above the register's smallest poll, so the lever could
not be perturbed at all. Moving it made the lever sweepable **and live**, and the
`EXPECTED_INERT` entry written when it was unsweepable was carried across
unchanged. A register entry is a claim about behaviour; this one described the
behaviour of the code before the change in the commit that made the change.

### Fixed

* The entry is deleted. `poll_min_n` is live at 2021 and the sweep now sees that.
* `_NO_METRO_POLL` carries a note saying what it is and is not true of, so the
  next lever added to the poll block is not filed behind it by reflex.
* `JUDGEMENT-CALLS.md` named `polling.validate` as the consumer — also left
  behind by §1.69's move — and is corrected to `polling.screen`, with the point
  that raising this floor withdraws the national polls the backtest depends on.

**No number moves.** The shipped floor is 300, every admitted poll is above it,
and the failure was in a claim about the lever rather than in the lever.


---

## 1.77 §1.70's instruction, carried out: every quoted number re-read on sixteen city-years (2026-08-23)

§1.70 ended with a standing instruction and nobody had acted on it:

> **Every number in this repository predating this entry was measured on nine
> city-years and must be re-read on sixteen before it is quoted again.**

Three guards were red at HEAD because of it, and had been for a day. None of
them was a defect in the model; all three were the record failing to move with
it, which is the one rule `CLAUDE.md` puts above the others.

### 1. `SD_FLOOR`'s promotion does not survive the panel

§1.59 measured the conditional dispersion of log θ and promoted `SD_FLOOR` from
🟡 to 🟢 **on the top bin only**, on the strength of two facts: the measured
dispersion at or above 15% of the vote was 0.138 against a used 0.150 — inside
the cluster-bootstrap interval — and the floor bound on **20 of 37** such
observations, a majority. On sixteen city-years:

| ≥15% of the vote | nine city-years (§1.59) | sixteen (now) |
|---|---|---|
| observations | 37 | **64** |
| measured sd | 0.138 | **0.273** |
| 95% CI (cluster) | [0.084, 0.171] | **[0.136, 0.386]** |
| width the model uses | 0.150 | **0.158** |
| ratio | 0.92× | **1.73×** |
| on the floor | 20 (54%) | **26 (41%)** |

**The used width is still inside the interval, and that is now a much weaker
statement than it was.** At nine city-years the interval was 0.087 wide and the
model sat in the middle of it. At sixteen it is 0.250 wide and the model sits
near the bottom, with a point estimate 1.7× the width in use. Nothing about the
prior changed between the two measurements — the panel did, and the top of the
ballot now looks like the other four bins rather than unlike them.

**So the 🟢 comes off.** `SD_FLOOR` is back to 🟡 on the top bin: better defended
than the sentence §1.50 gave it, not defended by a measurement that lands on it.
It is not evidence the constant is wrong — 0.158 is inside the interval and the
floor still binds on two of every five top-of-ballot observations — it is the
withdrawal of a claim the doubled panel no longer supports. The direction is the
same as §1.59's second finding, which is now the finding at **every** size: the
θ prior is too narrow across the ballot, including at the top.

`test_the_floor_binds_at_the_top_of_the_ballot_and_only_there` asserted the
majority. It now asserts the structural claim its name makes — the floor binds
at the top, materially, and not in the small-party bands — with the magnitude
recorded here, next to the measurement that would refute it.

**And its other half found something small and real.** The same test required
that the floor bind on **nothing** below 5% of the vote, because §1.59's second
finding is measured against the fit and would be partly measuring the floor
otherwise. On sixteen city-years exactly one observation sits on it:
**MINORITY_FRONT at eThekwini, target 2011, at 4.7997% of the vote** — a fifth of
a point under the bin edge. The next smallest fitted width below 5% is 0.1773,
well clear.

The cause is worth naming because it is not "the floor is spreading". The
enlarged record admits a **target 2011** fit at all, and 2011 is the target whose
`sd_for` line is built on the least history — two prior cycles. It exists only
because §1.70 ingested the pre-2011 archives. So this is a boundary case in the
thinnest fold, and the assertion is now split accordingly: **zero** below 1%,
where 250 of the 314 sub-5% observations live and where the finding actually
rests, and at most one in fifty between 1% and 5%. Tightened where the claim
lives, loosened only at the bin edge, and the number is written down so a real
spread is still a failure.

### 2. Rule 8's two tables were nine-city-year tables

`ITERATING.md` rule 8 is the instruction the next iteration acts on, and its
figures are held against `data/processed/history.json` by
`test_the_documented_figures_match_the_committed_artefact` — a guard §1.44 built
after the same document had been wrong three times. It did its job and named the
disagreement precisely: *"rule 8 says ranks 1-3 n = 27; history.json says 48."*

| | nine | sixteen |
|---|---|---|
| ranks 1-3 | n=27, PIT 0.483, probit-SD 0.685 | **n=48, 0.511, 0.676** |
| ranks 4-12 | n=37, PIT 0.676, probit-SD 0.695 | **n=56, 0.613, 0.828** |
| ranks 1-3 vote error | +10.62pp / 61.09pp | **+12.55pp / 94.23pp** |
| ranks 4-12 vote error | −22.76pp / 48.42pp | **−26.57pp / 72.60pp** |
| ranks 13+ vote error | +5.60pp / 16.89pp | **+4.42pp / 22.44pp** |
| phantom | +6.54pp | **+9.60pp** |

**The central claim survives, and this is the first out-of-sample test it has
had.** Rule 8 says the model over-forecasts the top three and under-forecasts
the middle, and that this is a zero-sum transfer rather than two faults. Both
hold on a panel half of which is a cycle the model had never been scored on:
the signs are unchanged, the ordering is unchanged, and +12.55 + 4.42 + 9.60
still balances −26.57 exactly.

The width statistic moved the other way and is worth flagging rather than
burying: probit-SD at ranks 4-12 goes **0.695 → 0.828**. Nothing about the width
was changed between the measurements, so this is what the middle band's
dispersion actually looks like over two cycles instead of one — closer to 1.0,
which is the calibrated value, and further from the "too wide by a factor" story
the nine city-years told.

### 3. The 2026 golden had been red since 22 August

`test_drawer`'s recorded marginals were last re-recorded 2026-08-17. Two shipped
changes moved the Johannesburg 2026 forecast after that — the σ_poll rebuild and
the single-house cap (§1.67–§1.69), and the panel doubling (§1.70) — and neither
carried the golden. It has been failing ever since, which is the same loss as a
silent re-record: **a test everyone expects to fail is a test nobody reads.**

Re-recorded deliberately, with the movement and its causes written into the file
per `CLAUDE.md`. ANC 21.28% → 22.82%, DA 24.51% → 25.79%, ASA 14.12% → 12.54%.
Exactly one component is isolated — restoring §1.75's six files is worth ANC
+0.39pp, DA +0.33pp, ASA −0.40pp — and the remainder pools the poll rebuild with
the other five metros' pre-2011 history. Those two were not separated, because
separating them means withholding archives from `data/raw/elections/` and that
is the operation §1.75 exists to make hard.

### What this costs and what it buys

**No model change, no lever moved, no score claimed.** The panel is 384 coherent
and CRPS 329.4 on sixteen city-years, identical to §1.70's, measured on the
restored tree.

What it buys is that the three instruments this project steers by — the
dispersion measurement, rule 8's calibration tables, and the golden — now
describe the model that exists. What it cost is a day in which the published
scoreboard, the documented rank bands and the recorded 2026 forecast were each
quoting a model that no longer ran, while the suite reported the fact in a form
nobody read.

**The general lesson is §1.70's own, and it is worth stating as a rule:** an
entry that doubles the evidence base must re-measure everything quoted off the
old one **in its own commit**, or it silently invalidates the record it did not
touch. Every one of these three was found by a guard that was already there and
already failing.


---

## 1.78 The loss is dated to a four-hour window, and everything measured inside it is re-run (2026-08-23)

§1.75 established that six raw inputs left `data/raw/elections` between §1.70's
measurement and its commit. It could not say **when**, so it could not say what
else was measured against the damaged record. This does.

### Dating it

`levels._citywide` can be monkeypatched to return `{}` for exactly those six
paths, which reconstructs the damaged tree **in memory, touching no file**. Run
`theta_residual` under it:

| | n | at ≥15% | on `SD_FLOOR` | sd at ≥15% |
|---|---|---|---|---|
| state A (restored, today) | 403 | 64 | 26 | 0.273 |
| state B (reconstructed) | **370** | **58** | **16** | **0.206** |
| **§1.71 as published** | **370** | — | — | **0.208** |

**§1.71 was measured in state B.** Its n=370 is not a rounding difference or a
different script — `theta_residual.py` has not changed since 20 August — it is
the damaged record, exactly.

The same technique settles the live forecast. Comparing party medians and 5/95
intervals for all 22 parties:

| comparison | parties whose statistics differ |
|---|---|
| state A run 1 vs run 2 | **0 of 22** |
| committed `forecast_summary.json` vs state A | **4 of 22** |
| committed vs reconstructed state B | **0 of 22** |

So `forecast_summary.json`, written **22 Aug 13:32**, was built in state B. And
`history.json`, written **09:43**, reproduces state A to the seat. **The six
files left between 09:43 and 13:32 on 22 August**, and everything derived after
09:43 is suspect.

### A caveat on reproducibility, because the obvious check does not work

Two runs of the same seed, same draw count and same tree are **not**
byte-identical. 201 leaves differ, all inside `scenario.theta_prior`, at the
last representable digit (1.0776853790229006 against …008) — floating-point
summation order, the same effect `CLAUDE.md` records for the parallel
`compare_history` at 6.7e-15.

**So byte-equality is the wrong instrument for a Monte Carlo artefact here, and
none of the above rests on it.** A seeded draw stream IS reproducible — that is
why the golden pins `numpy 2.5.1`, and `test_drawer_is_deterministic_for_a_fixed
_seed` passes — but the JSON around it is not. What is stable is the party
statistics, and the table above uses those: run-to-run noise is zero parties, so
a four-party difference is signal. Bit-equality was used in exactly one place
where it is the right standard — the γ fold 3 refit (§1.75), a least-squares fit
rather than a simulation.

### Re-run and re-scored

* **`forecast_summary.json`, `seat_draws.csv`, `coalition_*.csv`,
  `ward_winner_probs.csv`, `ward_paths.json`** — regenerated at 1500 draws, seed
  20261104, on the restored tree. **Every median is unchanged** (DA 79, ANC 63,
  ASA 24, EFF 23, MK 22, PA 19); four interval endpoints move by one seat — DA
  p95 108→110, MK p95 54→55, PA p95 31→30, ANC p5 25→24. A provenance
  correction, not a forecast change.
* **`data/processed/joburg/2021/*`** (written 13:08) — same batch, regenerated.
* **§1.71's dispersion figures** — corrected in §1.77 and in `JUDGEMENT-CALLS.md`
  before this entry was written.
* **The published site is NOT affected.** `site/*.html` is from 17 August, older
  than the ingest and older than the damage.
* **`history.json` / `history.md` needed nothing** — state A, verified.

### §1.74's Type A measurement, re-run in state A

§1.74's arm was measured in state B and compared against a baseline of 280 taken
from §1.70 — a **state-A** number. The comparison was therefore across two
trees. Re-measured properly, both arms in state A, 1500 draws:

| | no filter | Type A filter | change |
|---|---|---|---|
| sixteen city-years | 384 | **360** | **−24** |
| §1.70's original nine | 280 | **262** | **−18** |
| CRPS | 329.4 | **320.3** | **−9.1** |

Held-out NLL, same tree:

| target | no filter | Type A | |
|---|---|---|---|
| 2006 | −0.5555 | −0.5555 | unchanged |
| 2011 | 5.5915 | 5.5915 | unchanged |
| 2016 | 0.7531 | **0.8611** | worse |
| 2021 | 0.2280 | **0.0036** | better |

**The verdict is unchanged and the numbers are not.** Condition 1 required both
folds to improve; 2016 still worsens, so it is "undetermined" under §1.61.
Condition 2 required the nine to fall below the pre-ingest 254; 262 does not.
**REFUTED stands.**

But §1.74 recorded the filter as worth 20 seats on the nine against a baseline
from another tree, and it is worth **18 against its own**, with CRPS improving
9.1 — which §1.74 could not see, because a mixed comparison hides the size of
what it is comparing. The filter is a closer call than the entry made it look,
and it still does not clear a bar that was fixed in advance. That is the bar
working.


---

## 1.79 The inventory guard already existed. It was twelve days stale and wired to nothing (2026-08-23)

Asked for a guard that every data file is ingested and in use, the first thing
to check was whether one existed. **It did.** `src/archive.py` hashes every raw
input with its provenance into `data/archive_manifest.csv`, and that manifest is
one of only three files under `data/` that git tracks — deliberately, because
`data/**` is gitignored and its own docstring says the manifest "goes in git
even though the bytes do not".

It had been built on **10 August** and not since. It held **none** of the 21
files §1.70's ingest produced on the 22nd. And **nothing ran it** — no test, no
script, no hook.

**So it would not have caught the deletion**, and it is worth being exact about
why rather than claiming a near-miss: `--verify` reports files it knows about,
and it had never heard of the six. The failure was not that the tool was absent
or wrong. It was that the tool was **out of date and unwired**, which is the
same failure as the four blind guards of §1.75 one layer up.

### Why nobody ran it

Two reasons, both fixed.

**It exited 1 every time.** 44 of 393 files had no entry in
`archive.PROVENANCE` and were labelled `UNRECORDED -- add to src/archive.py`:
the 28 boundary extracts for the seven metros other than Johannesburg, the eight
per-metro `_metros/` result files, the six pre-2011 source zips, and Tshwane's
two clipped ward layers. Every one of them is documented in `SOURCES.md` — the
all-metro sweep of 2026-08-07 and the unlinked pre-2011 bulk export — so the
provenance existed and the table simply had per-JHB rows where it needed
prefixes. Added; it exits 0 on all 393.

**Its output is 90% noise.** The manifest covers `data/processed` as well, and
those files change on every run, so `--verify` reports ~100 differences that
mean nothing. The new tests therefore assert over **`data/raw` only** — inputs
are immutable, which is what makes them assertable — and say so in the file, so
the next person does not "helpfully" widen it and switch the guard off again.

### `tests/test_data_coverage.py`

Seven checks, three directions, wired into `run_all.py`:

| direction | check |
|---|---|
| recorded → present | `test_the_manifest_still_finds_every_raw_input_it_recorded` — **the §1.75 guard.** Existence and size on every run |
| present → recorded | `test_every_raw_input_on_disk_is_in_the_manifest` — keeps the manifest in date, without which the guard above checks a stale subset |
| content | `test_raw_input_hashes_match_when_asked` — full SHA-256, opt-in behind `ARCHIVE_VERIFY_HASHES=1` because re-hashing 517MB on every suite run buys little over size. Exercised once here: all 393 clean |
| expected → present | `test_every_election_the_record_expects_is_present_or_declared_absent` — the CALENDAR walk, moved here from `test_temporal`, which is about temporal leakage |
| declared → justified | `test_a_declared_absence_carries_a_reason_somebody_can_read` |
| **held → ingested** | `test_every_archive_the_ingest_can_key_is_ingested_or_declared` — if `ingest_historic.MUNI_HEAD` can key an archive, the file is derivable **today**, so no derived file means data on disk that nothing has ever read |
| **present → reachable** | `test_no_election_file_on_disk_is_unreachable` — a file no CALENDAR template can name. The mirror of §1.75: there a wanted file was absent; here a present file is invisible |

And, because a guard that only ever passes is indistinguishable from no guard,
`test_the_missing_input_guard_actually_fires` feeds the manifest check a row for
a file that is not there and requires it to fail — §1.75 in miniature, on every
run.

### What the two new directions found immediately

* **Five archives are held and have never been ingested**: `lge2000` for
  Tshwane, Cape Town, Mangaung, Nelson Mandela Bay and Buffalo City. The
  national CSV is in `_source/`, `MUNI_HEAD` has the municipality strings, and
  the ingest is deterministic — this is data the project holds and has not used.
  All five are declared in `levels.KNOWN_ABSENT`. **Ingesting them adds θ and ρ
  observations and moves every number here**, so it is a measurement to be run
  deliberately, not a chore, and it must not be done while §1.70's regression is
  open (task P2c).
* **Two files are unreachable and it is deliberate**: `lge2016_JHB_vd_party.csv`
  and `lge2021_JHB_vd_party.csv`, the original IEC downloads, kept because
  `data/**` is gitignored and they are the only copy of what was actually
  fetched. The model reads the parsed `_clean` files beside them, whose columns
  differ (`VotingDistrict` → `VD_Number`). Declared in `UNREACHED_BY_DESIGN`.

### One open question this raised, left open rather than closed quietly

`lge2011_JHB_vd_party_clean.csv` and `lge2011_TSH_vd_party_clean.csv` **changed
on 11 August** — 3.96MB → 3.23MB and 2.71MB → 2.18MB, about 19% smaller each —
between the manifest's build on the 10th and today. Both are 12 days older than
any current measurement, both reconcile, both carry only `PR` and `Ward` ballots,
and the model that reads them is green and verified. The commits either side
concern independents and ballot handling, which is a plausible cause and is not
evidence.

**The refreshed manifest now blesses the current bytes, and that is recorded
here rather than left silent**, because a manifest refresh is exactly the kind
of act that launders an unexplained change into a canonical one. Anyone
depending on those two files should establish the cause first; re-running the
ingest and comparing is the cheap way, and it is the technique that settled
§1.75.


---

## 1.80 State C pre-registered: the footprint exclusion, and the direction is already known (2026-08-23)

**Written and committed BEFORE the measurement.** This is §1.70's first
hypothesis, the last of its two still open, and the one §1.75 showed had never
been tested.

### The hypothesis, and why the obvious test is not one

§1.70 measured that doubling the panel cost **26 coherent seats on the nine
city-years that already existed** — 254 → 280, seven worse, two unchanged, none
better, against draw noise of ±2. It named the footprint as a candidate cause:
Mangaung and Buffalo City are keyed on `FS172` and `EC125` before 2011, their
pre-demarcation municipality codes, and the 2011 demarcation moved municipal
boundaries as well as wards. A ratio computed **across** 2011 for those two
divides a share of one area by a share of a different one.

§1.75 then found the tree had spent a day in a state where all six of their
pre-2011 files were missing, and measured it: **368 on the sixteen and 272 on
the nine, sixteen seats better, monotone, none worse.** That is not this test,
for the reason recorded there — it was not pre-registered, it left γ fold 3
fitted from files it removed, and above all **it over-excludes**.

### What state C is, exactly

The exclusion is on **(metro, transition)** pairs and nothing else:

| record | excluded | observations |
|---|---|---|
| θ | MAN `npe2009 → lge2011` | 8 |
| θ | BUF `npe2009 → lge2011` | 8 |
| ρ | MAN `lge2006 → lge2011` | 6 |
| ρ | BUF `lge2006 → lge2011` | 5 |
| | **total** | **27** |

θ 410 → 394, ρ 292 → 281, confirmed against the harness before this was written.

**State B removed 44.** The extra 17 are MAN and BUF's `npe2004 → lge2006` θ
observations, whose two endpoints sit **both inside the old footprint** and are
therefore clean by the very argument being tested. (`lge2000` does not exist for
either metro, so their ρ pre-2011 is only the crossing pair, and there state B
and state C agree.)

### The bar, fixed in advance

The same bar §1.74 set for the rival Type A hypothesis, so the two are
comparable, **plus one condition that only this hypothesis can fail.**

**Condition 1 — held-out NLL must improve in BOTH folds (2016 and 2021).**
One-of-two is "undetermined" under §1.61 — the verdict §1.62's two refits and
§1.74's Type A both received. The bar exists so a coin flip cannot be reported
as a win.

**Condition 2 — coherent seat error on §1.70's original nine must fall below the
pre-ingest 254.** State A is 280. Recovering four seats is not the claim;
recovering the regression is.

**Condition 3, and it is the discriminating one — state C must be at least as
good as state B on the sixteen: ≤ 368.**

Condition 3 is the whole point, and it is why knowing state B's number does not
give this test away. **If the demarcation is the mechanism, removing only the 27
contaminated observations must do at least as well as removing those 27 plus 17
clean ones.** State B threw away good data and still gained; if state C — which
keeps that good data — cannot match it, then what helped was dropping pre-2011
observations *in general*, and the cause is recency or quantity, not the
footprint. That is a different finding with a different fix, and §1.75 already
named it as the leading alternative.

### Stated in advance, because it is true and would otherwise look like hindsight

**The direction is already known.** State B is 16 coherent seats better on the
sixteen and 8 better on the nine. A bar set after seeing that is not the same
instrument as one set blind, and pretending otherwise would be worth less than
saying so. Conditions 1 and 2 were fixed by §1.74 before any of this; condition 3
is new and is set **against** the known number rather than below it, which is the
only way a known direction can still be informative.

### Two limitations, recorded now rather than discovered later

* **γ fold 3 is NOT excluded.** For MAN and BUF it is fitted on `npe2009 →
  lge2011` at VD level — the same crossing. Removing it would refuse both metros'
  2016 targets and drop the panel from sixteen to fourteen, which is not
  comparable to anything. §1.70's hypothesis is about the θ record, so this
  tests that; a γ-level version is a different and broader experiment.
* **This is an L1 specification choice on the scoreboard.** Rule 10 permits it
  only because the exclusion has independent justification — `DATA-QUALITY.md`
  item 13 documented the footprint before any of this was measured, and the rule
  is keyed on the demarcation date rather than on any residual.

### What each outcome means

| outcome | reading |
|---|---|
| all three conditions | the footprint is the mechanism; ship the exclusion as a declared, settable rule |
| condition 3 fails (state C worse than state B) | **the footprint is refuted**; the gain is from dropping older observations generally, and the question becomes recency weighting |
| 3 holds, 1 or 2 fails | the mechanism is real but too small to clear a bar set in advance; record and do not ship |


---

## 1.81 State C measured against its pre-registered bar: the mechanism is REAL and it is SMALL (2026-08-23)

Measured against §1.80, committed before the run. **Condition 3 passes.
Conditions 1 and 2 fail.** By §1.80's own outcome table that reads: *the
mechanism is real but too small to clear a bar set in advance; record and do not
ship.* Nothing is adopted; `EXCLUDE_DEMARCATION_CROSSING` stays off.

### The measurement, 1500 draws, all three states on the restored tree

| | A — default | B — §1.75's over-exclusion | **C — crossing pairs only** |
|---|---|---|---|
| observations removed | 0 | 44 | **27** |
| **sixteen city-years** | 384 | 368 | **368** |
| §1.70's original nine | 280 | 272 | **274** |
| **CRPS** | 329.4 | 329.0 | **324.7** |

Per city-year, A → C: seven better, one worse (eThekwini 2021, +2), eight
unchanged.

### Condition 3 — PASSES, and it is the informative one

**State C matches state B's 368 exactly, using 17 fewer exclusions, and beats
both on CRPS by 4.3 and 4.7.**

This is what §1.80 said would identify the mechanism. State B threw away MAN and
BUF's `npe2004 → lge2006` observations along with the crossing pairs — 17
observations whose endpoints both sit inside the old footprint and which the
demarcation argument does not reach. Removing them buys **nothing on seats and
costs CRPS**. So the crossing pairs carry the entire seat gain and the clean
observations were doing useful probabilistic work.

**The footprint is a real, correctly identified defect in the record.** That is
a genuine result and it is the first direct evidence for §1.70's first
hypothesis.

### Condition 2 — FAILS, and this is the one that matters

The bar was the original nine falling below the **pre-ingest 254**. State C
reaches **274**. It recovers **6 of the 26 seats** the panel doubling cost.

So the footprint explains **under a quarter** of the regression, and about
twenty seats of it are something else. §1.75 named the candidate and this
sharpens it: the record weights an observation by `_reliability(share)` — how
much of the vote it was measured off — and by nothing else. There is no recency
term anywhere in the level layer, while ρ, the spine and the poll aggregate all
have one. A transition three cycles back is pooled as the equal of one cycle
back.

> **BOTH SENTENCES ABOVE ARE WITHDRAWN (2026-08-23, §1.82).**
>
> **The comparison is false.** ρ and the spine use the *same*
> `_reliability(share)`-only weighting θ does — `local_record` feeds `_shrunk`,
> and the spine's `w = k / (worth + k)` has no time term. `levels.py`'s own
> docstring states the policy: *"Recency is priced by construction, not by a
> term."* Only the poll aggregate has a decay, and it is a DECLARED constant.
>
> **And "by elimination" does not follow.** A remedy failed a pre-registered
> ship bar; the diagnosis was not refuted. §1.78 measures the Type A arm at 262
> on the nine and 360 on the sixteen — 18 of the 26 seats — on this tree.
>
> Recency was then tested directly and **refuted**: held-out NLL is
> *non-monotone* in the age of the record, and older observations repair what
> the 2009→2011 transition breaks. §1.82.

### Condition 1 — FAILS

Held-out NLL, committed estimator, same tree:

| target | state A | state C | |
|---|---|---|---|
| 2006 | −0.5555 | −0.5555 | unchanged |
| 2011 | 5.5915 | 5.5915 | unchanged |
| 2016 | 0.7531 | **0.9512** | worse |
| 2021 | 0.2280 | **0.2014** | better |

Wins one fold, loses the other — "undetermined" under §1.61, the same verdict
§1.62's two refits and §1.74's Type A received. The 2006 and 2011 folds are
untouched, correctly: a target's fit uses transitions strictly before it, so a
2011 transition cannot reach them.

### Why it is not shipped, when it is a genuine data-quality defect

Rule 10 permits this exclusion — it has independent justification, documented in
`DATA-QUALITY.md` item 13 before any of this was measured, and keyed on the
demarcation date rather than on any residual. So it *could* ship on the argument
alone.

It does not, for one reason: **the bar was fixed in advance and it was not met.**
A 16-seat gain on the sixteen with a split NLL and a nine-city-year total still
20 seats above the pre-ingest baseline is exactly the shape of result this
project has adopted before and had to retract. §1.80 set three conditions
precisely so that a real-but-small effect could be told apart from a fix, and it
did its job. The finding is recorded with its number so nobody rediscovers it.

**What would change this**: the exclusion becomes shippable if the recency
question is settled first and the footprint correction is then measured *on top*
of it. If most of the remaining twenty seats is recency, a record that already
discounts old transitions may make these 27 observations irrelevant — or may
make the footprint the only thing left. Either is worth knowing, and neither can
be read off this run.

### Disposition

* Nothing adopted. `EXCLUDE_DEMARCATION_CROSSING` is off by default and the
  committed panel is unchanged at 384 / CRPS 329.4.
* `DEMARCATION_CROSSING` stays in `levels.py` as a declared register with its
  evidence, so the next measurement does not rebuild it.
* ~~**§1.70's open decision is now closed.** Both hypotheses have been tested
  and neither accounts for the regression. The next question is recency
  weighting in the θ record~~ — **WITHDRAWN, §1.82.** The decision is NOT closed
  and recency is NOT the next question. Type A accounts for 18 of the 26 seats
  on this tree (§1.78), and this entry's own measurement shows the footprint and
  the party events are **competing descriptions of one defect**: applied
  together they score 366, *worse* than Type A's 360.
  The caution that did hold is the method one — a decay fitted on these
  city-years is a scoreboard fit under rule 10 — and following it is what
  settled the question cheaply. The record's own forward validation was asked
  first, and it **refused** a decay: held-out NLL is non-monotone in the age of
  the record. §1.82.


---

## 1.82 Recency is refuted before it was fitted, and §1.81's "by elimination" was invalid (2026-08-23)

An independent methodological review was commissioned on the open questions. It
found two errors in §1.81 and both are conceded here in full. The measurements
below were run to check it, and they confirm it.

### Correction 1 — the premise for recency was FALSE, and it is in two entries

§1.75 and §1.81 both argue:

> *"`theta_record` weights an observation by `_reliability(share)` and by nothing
> else. There is no recency term anywhere in the level layer, while ρ, the spine
> and the poll aggregate all have one."*

**The second half is wrong.** Read out of `src/levels.py`: `local_record` feeds
`_shrunk`, which weights by `_reliability(s)` and nothing else — the *identical*
weighting θ uses. The spine's blend is `w = k / (worth + k)` where `worth` is a
sum of `_reliability` weights, again with no time term. `levels.py`'s own
module docstring states the policy outright:

> **"Recency is priced by construction, not by a term."** *The local result is
> five years stale at polling day where the national is two. Each route is
> corrected by a ratio fitted over its own gap … Nothing further is owed.*

The only genuine decay in the stack is `POLL_HALF_LIFE_DAYS = 120.0`, itself a
typed constant the register carries as DECLARED. So the argument "everything
else has a recency term, θ should too" rests on one instance, and that instance
is undefended. **An asymmetry that does not exist was the stated motivation for
the next workstream.**

### Correction 2 — "closed by elimination" does not follow, and the arithmetic says so

§1.81 wrote that both of §1.70's hypotheses were closed and elected recency *"by
elimination"*. **Nothing was eliminated. A remedy failed a pre-registered ship
bar, which is a different fact.** §1.78 had already re-measured the Type A arm
on the restored tree at **262 on the nine and 360 on the sixteen, CRPS 320.3** —
18 of the 26 seats — and §1.74's own text says *"2009→2011 is beyond doubt the
source of §1.70's 26 seats."* Declining a fix is not refuting a diagnosis, and
§1.81 should not have stepped from one to the other.

### The forward validation refutes recency directly, and it is not a scoreboard fit

`THETA_WINDOW` was added to `levels.py` — a per-target window keeping only the
*k* most recent transitions, which `THETA_EXCLUDE_TARGETS` cannot express
because the same absolute year is the most recent transition for one target and
three cycles back for another. Held-out NLL, **same held-out observations in
every arm** (n=97 at 2016, n=138 at 2021), only the fitting record changes:

| window | record at 2026 | 2016 fold | 2021 fold |
|---|---|---|---|
| 1 — most recent only | 138 | **0.6487** | **0.0722** |
| 2 | 235 | 0.9033 | 0.5808 |
| 3 | 320 | 0.7531 | 0.2419 |
| unlimited | 410 | 0.7531 | 0.2280 |

**It is not monotone, and that is the whole finding.** If age were the defect,
NLL would rise with the window. Instead window 2 is the *worst* arm at both
folds and window 3 partially repairs it. At target 2021, window 2 is
`{2011, 2016}` and window 1 is `{2016}`: adding the 2009→2011 transition takes
the fold from 0.0722 to 0.5808, and adding two *older* transitions on top brings
it back to 0.2419.

**Older observations repair what the 2011 transition breaks.** A decay is
monotone in age by construction and cannot represent that. This agrees with
§1.71's dispersion table from the opposite direction — 2004→2006 sd 0.226,
2014-2021 sd 0.200, **2009→2011 sd 0.942** — where the oldest transition in the
record is as clean as the newest.

**Recency is refuted, on evidence independent of the seat score, before a
parameter was fitted to it.** That is the order §1.61 asks for and the reason it
cost one afternoon instead of a week.

### Four arms, one tree, 1500 draws

| arm | sixteen | nine | CRPS | 2016 cycle | 2021 cycle |
|---|---|---|---|---|---|
| A — default | 384 | 280 | 329.4 | — | — |
| C — footprint (§1.81) | 368 | 274 | 324.7 | −12 | −4 |
| **Type A (§1.78)** | **360** | **262** | **320.3** | **−10** | **−14** |
| **both together** | **366** | **268** | **320.5** | **−10** | **−8** |

**The two are not additive. They interfere.** Applying the footprint exclusion
*on top of* Type A costs 6 seats against Type A alone (366 against 360) and buys
nothing on CRPS. They overlap by construction — Type A removes COPE, the DA and
the IFP at the 2011 transition across all eight metros, and the footprint rule
removes Mangaung's and Buffalo City's entire 2011 transition, which contains
those same parties. Between them they take out too much of that transition for
those two metros.

**So the footprint and the party events are competing descriptions of one
defect, not two defects that sum.** §1.81's reading — that the footprint is real
and worth 6 seats *in addition* — does not survive this. It is worth 6 seats
*instead*, and Type A is the better instrument for the same contamination.

### Cycle replication, which is the honest test on two effective clusters

Both arms replicate — the sign holds in both cycles and neither cycle is a net
loss:

| arm | 2016 cycle | 2021 cycle |
|---|---|---|
| state C | 5 better, 0 worse, 3 unchanged | 2 better, 1 worse, 5 unchanged |
| Type A | 4 better, 3 worse, 1 unchanged | 6 better, 1 worse, 1 unchanged |

A paired bootstrap resampling metros gives state C −16 [−28, −4] on seats,
−4.64 [−7.94, −1.29] on CRPS and −1.54 [−3.17, −0.34] on vote MAE. **Those
intervals are anti-conservative and are not quoted as decisive**: eight metros
inside one cycle share a national swing, so resampling metros treats correlated
units as independent. The between-cycle replication above is the part that is
honest, because the two cycles are genuinely different elections.

### What this does to the record

* **Recency (task #36) is closed as a negative result** before any parameter was
  fitted. `THETA_WINDOW` stays as a declared harness, off by default.
* **§1.70's regression is substantially accounted for** — the 2009→2011
  transition, via party-structural events, at 18 of 26 seats measured.
* **The open item is the one §1.74 already named and nobody built**: *"Route, do
  not drop."* An exclusion moves the volatility out of the model's prior and
  into its error; §1.74 measured that failure precisely, with `sd_for` at 5-15%
  falling 0.203 → 0.150 while the measured dispersion stayed at 0.839.
* **Nothing is adopted here.** All three flags remain off and the committed panel
  is unchanged at 384 / CRPS 329.4.


---

## 1.83 The amended bar had a hole that would have shipped the thing we decided not to ship (2026-08-23)

The independent review was asked to critique `PLAN-TO-LIVE.md`. It found a
defect in the **bar**, not the plan, and it is the more serious of the two.

### Applying the amendment as written, to the numbers §1.82 had just produced

| | Key 1 — paired, cycle-replicated | Key 2 — calibration floor | verdict |
|---|---|---|---|
| state C | 2016 5 better / 0 worse (−12); 2021 2 / 1 (−4) | CRPS 329.4 → **324.7** | **PASSES** |
| **bare Type A** | 2016 4 / 3 (−10); 2021 6 / 1 (−14) | CRPS 329.4 → **320.3** | **PASSES** |

**The bare Type A filter passes.** It is the one change §1.74, §1.82 and the
plan all agree must *not* ship — because an exclusion moves volatility out of
the model's prior and into its error, which §1.74 measured directly.

The old §1.61/§1.74 condition — *held-out NLL must improve in both folds* — was
the guard against exactly that, and the amendment dropped it while rewriting the
seat instrument. **Key 2 does not catch it**, and the reason is the diagnostic:
both rejected exclusions **improve CRPS while worsening the estimator's held-out
NLL at 2016** (Type A 0.7531 → 0.8611, state C 0.7531 → 0.9512). That divergence
is the signature of trading accuracy on the parties the model already handles
against accuracy on the parties it does not.

### KEY 4, added

> **The estimation record is a floor too.** Held-out NLL on `theta_residual`'s
> folds must not worsen in **either** fold. Not tradeable.

Keys 1 and 2 score the **panel**, where parties undergoing structural events are
a handful of columns among hundreds, on ~2 effective clusters. Key 4 scores the
**estimator on those parties**, on 18. It restores rule 11's logic to a bar that
had lost it.

It is a **floor** (must not worsen), not §1.74's **gate** (must improve in both
folds). A change may be NLL-neutral and ship on the panel; it may not ship while
making the estimator worse where the record is thickest.

**State C's disposition, stated rather than left on the floor:** passes Keys 1
and 2, **fails Key 4**, does not ship. Under the amended bar that is a clean
verdict rather than §1.81's judgement call — and §1.82's interference result says
it is a worse description of the same defect, not an independent gain.

### Two stale figures in the canonical artefact, one of them self-reproducing

**`compare_history` was TYPING a model figure into the report it generates.**
Every `history.md` carried the literal string *"quote the sign count as **8 of 9
city-years, 8 of which are one election**"* — a nine-city-year claim, still being
emitted onto a **sixteen**-city-year report, into the artefact every other
document is audited against, and which `build_site.py` then builds the public
pages from. `test_the_documented_figures_match_the_committed_artefact` parses
`ITERATING.md`'s two marked tables and **nothing parses generated prose**, so
§1.77's re-read could not reach it.

It now **computes** the count. Measured on the committed scoreboard:

> **12 wins, 2 losses, 2 ties across sixteen city-years — 2016: 7W 1L 0T;
> 2021: 5W 1L 2T.** The sign replicates across cycles.

That is a *better* claim than the one it replaces, and it is the one the amended
bar's own Key 1 asks of any candidate. The losses are Tshwane 2016 (18 against
uniform swing's 10) and Mangaung 2021 (10 against 8); eThekwini 2021 and Buffalo
City 2021 tie.

**And `ITERATING.md` rule 1 still said "42% off uniform swing inside Gauteng, 10%
outside"** — nine-city-year figures against the artefact's **30% and 24%**.
Corrected. Same cause: the audit covers rule 8's tables and nothing else.

`CLAUDE.md` says never type a model figure into prose. It was being done inside
the generator that produces the prose.

### What else the review changed in the plan

* **The plan's central claim was over-broad.** *"The model is good enough to ship
  today"* is true of a model and not of the 2026 configuration: a 48-seat channel
  the panel scores is **dark** at 2026 (no national poll in the register), a
  channel that decides the 2026 headline fires at **one** backtest city-year, and
  nine typed constants are live at 2026 and inert in every backtest. Rewritten so
  the configuration difference **leads** the page rather than sitting in a caveat.
* **B5 was scheduled inside the live window** — between the lists and polling day,
  on the tree that must produce the published revision, moving every number.
  Moved to **after 4 November**. §1.75 is the entry about what happens when the
  archive shifts under a live artefact.
* **A4 was badly under-scoped.** Eleven `mode="fixed"` tokens on the live front
  page are sourced to `run:turnout_tilt_da=1`, a lever `run_model` no longer has,
  and because they are fixed the drift audit is **silent by construction**. It is
  the only place this project currently publishes numbers it cannot reproduce.
* **The go/no-go moved from 1 September to 27 August** and is now gated on A1 and
  A2 being *done*, not on a date.
* **B1 is gated by an afternoon, not a week**: pre-register, then measure held-out
  NLL on both folds first — it runs on a fit, not 1500 draws, and on 18 clusters.
  Bare Type A fails that gate today.
* **B2 promoted** from chore to risk management: it is the only measurement that
  says how much of the November forecast is decided by typed constants.
* **Both B4 code defects confirmed** by reading the source. The `sd_for` covariate
  one moved into B1 as a prerequisite.

### The lesson, which is the same one twice

An amendment to a bar is a change to the model's acceptance criteria, and it
needs the same treatment as a change to the model: **state what it would have
decided about the cases already on the table.** Had that been done when the
amendment was written, the hole would have been visible in one line, because the
cases were already measured and sitting in §1.82.


---

## 1.84 Four parallel audits of the whole tree: a live lever was half-connected, and a city's bounds were leaking (2026-08-23)

The owner asked for the repository to be searched exhaustively — every file,
recursively, for anything inherited from the original model and for hidden
constants "sabotaging the new model invisibly", on the grounds that **nobody had
ever actually looked**. Four read-only audits ran in parallel over disjoint
scopes: code constants, reachability, root documents and site, and derived
artefacts. They were right that nobody had looked.

### The one that changes the live forecast: `poll_half_life_days` reached the WIDTH and not the CENTRE

`montecarlo` passed `scenario["poll_half_life_days"]` to `polling.effective_houses`
and `polling.aggregate_sd`, and passed **nothing** to `polling.aggregate` — which
is the function that produces the poll-blended **central shares**. So the centre
used `aggregate`'s hardcoded `half_life_days: float = 120.0` default argument.

**This is the `LEVEL_DF` shape for the third time**, and this instance is the
worst of the three because it is live at 2026. Measured on the two admitted
Johannesburg waves:

| half-life | ANC | DA | MK |
|---|---|---|---|
| 30 days | 0.1839 | 0.4190 | 0.1284 |
| **120 days (what was in force)** | **0.2160** | **0.4110** | **0.1150** |
| 365 days | 0.2317 | 0.4071 | 0.1085 |
| no decay | 0.2400 | 0.4050 | 0.1050 |

**5.6 points of ANC in the published forecast, across a lever no sweep could
reach.** And `test_levers_are_live` certified it live at 2026 the entire time —
correctly, because it *does* move the forecast, through the σ path. That is
exactly how it hid: the existing guard asks whether a lever moves the forecast
at all, not whether it reaches every consumer the register implies.

**Fixed and number-neutral at the shipped default.** `aggregate` now takes
`half_life_days: float | None = None` and resolves to `POLL_HALF_LIFE_DAYS` at
call time — the shape `aggregate_sd` beside it already had — and the call site
passes the scenario key. Verified byte-identical to the old behaviour at 120.0,
and verified the lever now bites at 30.0.

`asof` is deliberately **not** aligned in the same change. The σ path uses
`target.date` and this uses the newest fieldwork date; aligning them is arguably
more correct and it *moves the numbers* at float level, so it is a separate
decision rather than a free rider. Recorded in the call site.

**A new guard, and it is proved not blind.** `test_no_lever_is_passed_to_one
_consumer_and_withheld_from_another` walks `montecarlo`'s AST, finds every
scenario key forwarded to a `polling` function, and fails if the same key is
withheld from another consumer that accepts it. Run against a reconstruction of
the pre-fix call site it reports `poll_half_life_days → aggregate`; run against
the fixed tree it passes.

### The second real bug: `export_interactive` published Johannesburg's θ bounds for every city

`apply_city` **rebinds** `montecarlo.PLAN_BOUNDS` (`PLAN_BOUNDS = city.plan_bounds`)
rather than mutating it — unlike `DEFAULTS`, which is cleared and updated in
place on the two lines above. `export_interactive.py` did
`from montecarlo import DEFAULTS, PLAN_BOUNDS`, so the two names on one import
line behaved differently: `DEFAULTS` tracked the city and `PLAN_BOUNDS` stayed
pinned to the module literal. Every non-Johannesburg export published
Johannesburg's θ ranges.

This is the un-namespaced-output hazard the project already has a memory note
about. Fixed by reading `montecarlo.PLAN_BOUNDS` through the module.

### Guards that could not fire

* **`tests/test_pool_bounds.py` called `skip()` without importing it** — the
  only undefined name in 69 files. Masked only because `history.json` is
  committed; on a fresh clone the guard raised `NameError` instead of skipping.
  It had never once executed.
* **Five test files used a hand-rolled `for name, fn in globals()` runner** that
  catches neither `SkipTest` nor `SystemExit`, so the first skip aborted the file
  and every later test silently never ran — `test_regressions` alone has five
  `skip(` calls. Under `run_all.py` they were fine, because the suite supplies
  `run_module`. **The suite hid it**, which is the same sentence this log wrote
  about two other defects yesterday. All five now use `run_module`.

### What the audits found and this entry does NOT fix

Recorded so they are decisions rather than oversights, and carried into
`PLAN-TO-LIVE.md`:

* **The register's guard is structurally blind** to numeric default arguments,
  dataclass fields, dict-valued constants, lowercase constants, inline literals,
  argparse defaults and every number in a TOML file. It inspects 53 names. That
  is why everything above was reachable.
* **Unregistered constants that decide real things**: `overhang_rule` (a legal
  interpretation that sets council size, string-valued so the guard skips it),
  `GAMMA_FOLD`, `PLAN_BOUNDS`, `w_recency = 0.70` and `kappa_bye = 0.25`
  (argparse defaults, verbatim from the original plan, baked into 20 committed
  `turnout.csv` files that carry no artefact key), `--w-split = 0.6`, three
  numbers in `config/dimensions.toml` including `min_oos_gain` which decides
  which census dimensions exist at all, and nine arrival-path selection
  constants.
* **Six of eight metros run with `PLAN_BOUNDS` empty**, so the θ clamp is absent
  and its violation counter reports zero — the panel cannot test that constant
  and does not say so.
* **`montecarlo.__small__`**: two typed `0.8`s read off a `"small"` key that does
  not exist anywhere in `levels.py`, building a fabricated 10th/90th band, into a
  dict entry nothing reads. Inert; a trap.
* **`data/processed/regime_cap_summary.json` feeds a live stat token** and was
  produced on 7 August by a model that still had `turnout_tilt_da` in it — the
  exact lever `CLAUDE.md` names as having put ten stale claims on the page.
  `stats.py` applies no freshness check to a source file.
* **`forecast_summary.json` carries no provenance at all** — no city, no target,
  no time, no code hash — while `pools_*.json` has had an `artefact_key` since
  §1.70.
* **`vd_ward_<year>.csv` and `vd_concordance.csv` are written at city level and
  read at target level**, so 14 files are unreadable where they sit; and
  `fold.py` hardcodes Johannesburg's concordance for every city.
* **`gamma_recent.csv` exists for 5 of 20 city-year directories**, so most of the
  panel falls silently to γ = 1.0 where Johannesburg takes a measured value.
* **`build_all.py` cannot reach `build_site` or `build_portal`**, because
  `build_interactive.py` raises at module level and the runner treats any
  non-zero return as fatal. The documented one-command build has been severed.

### Cleared out

`archive/` now holds the original plan (`.md` and its 13.6 MB `.pdf`, both
duplicated verbatim in `MODEL-LOG.md` Appendix A), `METHODOLOGY.md`,
`EXPANSION.md`, `model-review.html` — which describes the **expand** rule and was
linked from the live review page as *"the full technical audit"* — the frozen
interactive, the four served-but-unbuilt `site/drafts/` pages, and
`scenarios/joburg-pools.json`, a tracked, documented, executable scenario file
describing the bloc design deleted on 2026-08-10. Eighteen unread derived
artefacts moved out of `data/processed`. `.wrangler/` untracked and gitignored.

Each has a row in `archive/README.md` saying what superseded it. Nothing was
deleted: removing a superseded document destroys the record of why it was made.


---

## 1.85 The §1.84 fix was written against the instance, not the class — and the class guard found two more (2026-08-23)

A third independent review of `PLAN-TO-LIVE.md` reproduced §1.84's headline
finding exactly — ANC 0.1839 / 0.2160 / 0.2317 / 0.2400 across the half-life
range — and then made a criticism of the **fix** that is correct and is this
project's own recurring lesson turned back on it.

### The criticism

> *The fix commit converted one of twelve literal fallbacks and left eleven, in
> the commit whose entire subject was that two paths had resolved one lever
> differently.*

`montecarlo` writes each lever's value a second time as a literal at the call
site — `scenario.get("poll_half_life_days", 120.0)`. §1.84 fixed the one call
that had no key at all and left the pattern everywhere else. Inert today,
because `scenario` is always built from `DEFAULTS`. **Which is exactly what was
true of `LEVEL_DF` before it wasn't.**

And the new guard was worse than the pattern it policed: it iterated a
three-name allowlist `("aggregate", "aggregate_sd", "effective_houses")` over
one module. `DATA-QUALITY.md` item 13 already says the sentence — *"a guard
written against one route through a function is not a guard on the function"* —
and it was written about `matches_city` two days earlier.

### The class guard, and it found two things immediately

`test_every_literal_fallback_equals_the_declared_default` walks every `.py` in
`src/`, finds every `scenario.get("<key>", <numeric literal>)`, and asserts the
literal equals `DEFAULTS[key]`. No allowlist, 14 call sites checked, and it
fails if it ever finds none — a guard that checks nothing must not pass.

**It failed on the run that introduced it:**

    montecarlo.py:2314  scenario.get('contestation_expand', 0.0)
                        but DEFAULTS['contestation_expand'] = 0.22

The literal is the **identity** — no contestation expansion at all — against a
declared 0.220. Benign today because the key is always present, and the trap is
the same shape as the one §1.84 fixed: had it ever fired, the computation would
have applied no expansion while the message printed eleven lines below reported
0.220 from the same scenario. Corrected to fall back to `DEFAULTS`.

### Widening the second guard found a third thing, and the answer was a cleanup already owed

With the allowlist replaced by *every public callable in `polling`*, the guard
reported `poll_min_n` reaching `screen` and not `validate_or_die`. That one is a
**correct** withholding — §1.69 deliberately moved the sample-size floor from
validation to screening, because a small poll is well-formed-but-inadmissible
rather than malformed.

But the reason it could be reported at all is that `validate` and
`validate_or_die` still *accepted* `min_n` and ignored it. Its own
`DELIBERATELY_UNUSED` entry said so, and said what to do:

> *"Removing it would be the right cleanup once nothing passes it."*

Nothing passes it — verified across `src/` and `tests/`. So the parameter is
gone from both signatures and the excuse is deleted. **An argument accepted and
ignored is a trap, not an API**, and carrying an excuse for one is how it
survives.

### What is now guarded, and what is honestly not

| guard | covers |
|---|---|
| `test_every_literal_fallback_equals_the_declared_default` | the whole class, mechanically, no allowlist |
| `test_no_lever_is_passed_to_one_consumer_and_withheld_from_another` | every public `polling` callable, with documented-exemption support |

The second still **cannot** see keys forwarded through a `**kwargs` splat,
forwarded positionally, or consumed outside `polling`. That is written into its
docstring rather than left for the next reviewer to discover.

### Two corrections to §1.84 and the plan

* **`forecast_summary.json` does NOT have "no provenance at all."** Its
  `scenario` block carries `_pools_artefact_key`, `_pools_stale` and
  `_constants_read`. What it lacks is city, target, timestamp and a code hash.
  The gap is smaller than claimed and belongs inside A1's hash-and-freeze.
* `gamma_recent.csv` exists for 5 of **18** city-year directories, not 20.

### And one finding four audits and I all missed

**There is a second house's Johannesburg reading in the register, it passes the
screen, and a scope string discards it.** `ipsos-w2-2025-metros` is admitted by
`polling.screen`; `montecarlo` then filters `scope == "metro"` and drops it,
because its scope is `metro-aggregate`. Measured:

| | H_eff | ANC | DA |
|---|---|---|---|
| as shipped (SRF only) | **1.00** | 0.2160 | 0.4110 |
| including the aggregate | **1.46** | 0.2424 | 0.3792 |

**2.65 points of ANC and 3.18 of DA, and the difference between one house and
1.46.** Excluding a multi-metro aggregate from a single-metro estimate is
defensible — it is not a Johannesburg reading. What is not defensible is that
the decision is **unregistered, undocumented, and sits directly on the project's
single largest declared risk.** A2 cannot honestly print "one house" without
also printing the second reading it declined and why.

Not changed here. Registered as a decision to be made and published, in the plan.


---

## 1.86 C1: the register's guard could see 53 names. Widened, it named seventeen more (2026-08-23)

The first item of `PLAN-TO-LIVE.md`'s Track C, and it is first for a reason the
plan had to be corrected to state: **Key 3 of the amended bar computes
Derivedness Debt *from* the register**, so a register that cannot see a constant
prices it at nothing. C1 blocks B2, and B2 feeds A2's disclosure.

### What it could not see

`test_every_tunable_constant_is_in_the_judgement_register` inspected top-level
`ast.Assign`, single target, UPPERCASE, `literal_eval` to a bare `int`/`float`.
**53 names.** Structurally blind to:

* **numeric default arguments** — the `LEVEL_DF` shape, three instances, the
  latest costing 5.6pp of ANC in the live forecast (§1.84);
* **argparse defaults** — where `w_recency = 0.70` and `kappa_bye = 0.25` have
  sat since the original plan;
* **container constants** — `PLAN_BOUNDS`, `GAMMA_FOLD`;
* **non-numeric `DEFAULTS` values** — `overhang_rule`, a *string*, which sets
  the council size and the majority threshold;
* **dataclass fields**, and **every number in a TOML file**.

### Three filters, each a rule rather than a list

Widening it naively surfaces 144 hits, most of them noise. Three principles cut
that to 26:

1. **run control is not belief** — `draws`, `seed`, `jobs`, `tolerance`;
2. **a counter initialised to zero is not a claim** — `ModelRun`'s accumulators
   start at 0 because that is what accumulators do;
3. **a container is a judgement only if it CONTAINS NUMBERS** — a table of
   column names or file paths is structure; a table of bounds is belief.

The third is the one that does the work: it takes 56 container constants down to
10, keeping `PLAN_BOUNDS` and `GAMMA_FOLD` while dropping `COLUMNS`,
`PROVENANCE`, `ELECTIONS` and the rest of the structural tables. An `EXEMPT`
list then names the operational residue — HTTP timeouts, the map simplifier, a
solver's iteration count — each with a reason.

### The seventeen

Registered in `JUDGEMENT-CALLS.md` §H, all 🔴 except one. The ones that matter:

| constant | why it matters |
|---|---|
| **`overhang_rule = "deduct"`** | a legal interpretation setting council size and the majority threshold; four regimes give four answers. Invisible because it is a string |
| **`PLAN_BOUNDS`** | the plan's θ table. **Six of eight metros have no `[judgements]` block**, so the clamp is silently absent — four panel city-years run with it and twelve without, which makes 384 a mixture of two configurations |
| **`GAMMA_FOLD`** | which fold the live forecast reads; the code concedes *"the constraint alone does not pick one"* for 2026 |
| **`min_oos_gain = 0.01`** | the bar a census dimension must clear **to exist at all** — age and sex are rejected by it, so it is upstream of every pool. `dimensions.toml` was not mentioned in the register once |
| **`w_recency = 0.70`, `kappa_bye = 0.25`** | verbatim from the original plan, whose own text asks for a sensitivity test `MODEL-LOG` never records, and reaching the model through 20 `turnout.csv` files with **no artefact key** |
| **`total_seats = 270`** | Johannesburg's council as a **default argument in the shared allocator**; `leverage.py` omits it and allocates any city into a 270-seat chamber |
| **`BINS`** | the size bands producing §1.59/§1.77's headline — the "≥15%" cut quoted as natural is a chosen threshold |

### What this does and does not achieve

**It changes no number.** Every constant listed was already in force; the guard
simply could not see it. What changes is that B2's sweep now has a list, and the
Derivedness Debt is computed over the constants that exist rather than over the
53 the old detector happened to match.

**And it is honest about what is still invisible**: inline literals inside
function bodies are not covered. That is a much larger surface — `pools.py`
alone has nine arrival-path constants inline — and it needs a different
instrument, because a bare `0.25` in an expression has no name to register. It is
recorded as the remaining gap rather than quietly omitted.


---

## 1.87 σ_poll pre-registered for replacement: two terms, one of which never shrinks (2026-08-24)

**Written and committed BEFORE the measurement.** The owner said plainly that he
was not convinced by the poll logic and commissioned a search of how PR-system
forecasters actually do this. The research came back against us on structure, not
just on values.

### Why the current form is wrong, and it is not a matter of taste

**1. The decomposition cannot be identified.** Dominitz & Manski, *JASA* 121(553)
(2025), compute a Total Margin of Error for a 1.4%-response-rate poll: **49.3pp
with no assumptions about non-respondents**, 4.9pp under a strong one. Every
number a component decomposition emits is a restatement of the priors put in. Our
four components multiply priors without adding information. And the model the
research points to — Shirani-Mehr et al. (2018) — uses **two** terms,
`σ² = p(1−p)/n + τ²`, with historical averages as the proxy for τ.

**2. We divide the common term by the number of houses. It does not shrink.**
Verified in our own code — `aggregate_sd` ends:

    return math.sqrt(sampling_sq
                     + (POLL_HOUSE_SD ** 2 + screen ** 2 + drift ** 2) / h_eff)

Everything but sampling is divided by `h_eff`. Measured on our own register by
cloning the two SRF waves across synthetic houses:

| houses | 1 | 2 | 4 | 10 | 100 |
|---|---|---|---|---|---|
| σ | 4.01pp | 2.83pp | 2.00pp | 1.27pp | **0.40pp** |

**Our model says that with enough pollsters a poll becomes almost certain.** The
literature says the opposite in three independent places: Jackman (2005) —
*"if the biases run in the same direction, then the gain in precision from
pooling results in higher levels of confidence about a biased estimate"*;
Shirani-Mehr et al. — *"shared election-level poll bias persists unchanged, even
when averaging over a large number of surveys"*; and The Economist's production
code carries a 1.3pp bias vector correlated ρ=0.9 that never shrinks.

**3. `POLL_HOUSE_SD` is a residual of one house.** It is defined as
`√(3.03² − sampling²)` on nine Ipsos 2016 readings — which are also, circularly,
the only metro-poll test cases the backtest has.

**4. The half-life is four times the longest documented value.** Israel and
Denmark 2–14 days, New Zealand 30. Ours is 120, worth 3.2 points of ANC.

**5. The cap is doing almost nothing.** It moves the DA's weight by 0.023, while
538 prices a house with no track record at **+0.66pp of error**, not a halving of
weight.

### The replacement, with every constant sourced from outside this repository

    σ = sqrt( sampling² / waves          # deff 1.6 kept, declared as a FLOOR
            + σ_common²                  # 1.5pp — NEVER divided by h_eff
            + σ_idio² / h_eff            # 1.5pp — the only term that shrinks
            + (0.30·√days)²              # drift since fieldwork
            + 0.8² )                     # SA volatility adjustment

and **`weight_cap` is deleted**, replaced by the floor that `σ_common` now
provides.

| constant | value | where it comes from |
|---|---|---|
| `σ_common` | 1.5pp | Finland 1.25, The Economist 1.30, Selb et al. 1.5 (German mean absolute bias, 5,240 polls), SA 2024 1.66 |
| `σ_idio` | 1.5pp | Stoetzer prior N(0,1); Bon et al. ≈1.0; Jackman phone-only 1–3; SA 2024 1.71 |
| drift | 0.30 pp/√day | band 0.20 (Ellis NZ, *estimated*) to 0.41 (from Jennings & Wlezien's horizon profile). Current 0.10 is 2–4× too small |
| volatility | +0.8pp | +0.1pp per 1pp of average party swing |
| deff | 1.6 **unchanged** | Shirani-Mehr fn.2 measures 1.7, IQR 1.4–2.0. The reviewer retracted its own earlier advice to change this |

### Why the test is better than it looks

The metro poll path fires at exactly three backtest city-years — **Johannesburg
2016, Tshwane 2016, Nelson Mandela Bay 2016** — and those are *the nine readings
`POLL_HOUSE_SD` is calibrated on*. Under the current form, testing there is
circular.

**Under the replacement it is not.** `σ_common` and `σ_idio` are taken from
Finnish, Danish, German, American and New Zealand evidence, and no longer from
the 2016 residual. So those three city-years become a genuine held-out test set
for the first time. That is a real gain independent of which formula scores
better.

### The bar, fixed in advance

Judged under `ITERATING.md`'s amended four keys.

* **Key 1 — paired, cycle-replicated.** The poll path fires on one cycle only, so
  cycle replication is unavailable and **Key 1 cannot pass**. It must therefore
  not *fail*: the change may not make the sixteen-city-year total worse beyond
  noise.
* **Key 2 — calibration is a floor.** CRPS must not worsen. **This is the key
  that should decide it**, because the change is about the WIDTH of the poll's
  claim, and CRPS is the width-sensitive score. A wider, better-calibrated poll
  channel should improve CRPS even if seats barely move.
* **Key 4 — held-out NLL** must not worsen in either fold.
* **Key 3 — derivedness.** Strongly positive by construction: `POLL_HOUSE_SD`,
  `POLL_SCREEN_SD_UNDISCLOSED` and `POLL_HOUSE_K` are retired; every replacement
  constant carries a published citation. This is the first change to earn Key 3
  rather than spend it.

**Stated in advance so it cannot be claimed afterwards:** three city-years and
one house cannot settle whether these constants are right. What this measurement
can establish is whether the new form is *not worse* on the panel, and whether it
is better calibrated. If it is, it ships on Key 2 and Key 3 — on the argument
that its constants are sourced and its predecessor's were circular — and **not**
on a seat improvement it is too small to demonstrate.

### What would refute it

CRPS worsening beyond noise, or held-out NLL worsening in either fold. Either
means the wider poll channel is buying calibration nowhere and costing accuracy,
and the current form stays until more houses exist.


---

## 1.88 σ_poll measured against §1.87's bar: the panel cannot tell, which is what was predicted (2026-08-24)

Measured against the bar committed in §1.87 before the run. **It passes, and it
passes on the two keys the pre-registration nominated — not on a seat gain.**

### The measurement, 1500 draws, both arms on the settled tree

| | current | two-term | change | 95% CI (metro-clustered) |
|---|---|---|---|---|
| sixteen city-years, seats | 384 | **384** | **0** | [−6, +6] |
| sixteen city-years, CRPS | 329.4 | **329.2** | **−0.16** | [−1.41, +1.21] |

**Both are indistinguishable from zero.** Two city-years move and cancel exactly
— Nelson Mandela Bay 2016 −2, Tshwane 2016 +2.

On the three city-years the metro poll actually fires on:

| | current | two-term |
|---|---|---|
| seats | 50 | 50 |
| CRPS | 41.6 | **41.4** |
| Johannesburg 2016 | 22 seats, CRPS 20.0 | 22, **19.5** |
| Nelson Mandela Bay 2016 | 10, 8.1 | **8**, **7.9** |
| Tshwane 2016 | 18, 13.6 | **20**, 14.1 |

The whole CRPS movement is inside the poll-bearing city-years, which is at least
coherent — but it is 0.2 on a panel whose own interval is ±1.4.

### Against the bar

* **Key 1 — does not fail.** 384 against 384. As §1.87 stated in advance, Key 1
  *cannot pass* here: the metro poll path fires on one cycle only, so cycle
  replication is unavailable.
* **Key 2 — does not worsen**, and is very slightly better. §1.87 nominated this
  as the deciding key and said a wider, better-calibrated poll channel should
  improve CRPS even if seats do not. It did, by an amount the panel cannot
  resolve.
* **Key 4 — unaffected by construction.** `theta_residual.py` contains zero
  references to `polling`, so the poll change cannot move held-out NLL. Verified
  rather than assumed.
* **Key 3 — strongly positive.** `POLL_HOUSE_SD`, `POLL_SCREEN_SD_UNDISCLOSED`
  and `POLL_HOUSE_K` are retired. Every replacement constant carries a published
  citation from outside this repository. **This is the first change to earn Key 3
  rather than spend it.**

Neither refutation condition fired: CRPS did not worsen beyond noise, and NLL did
not move at all.

### What actually changed, and it is not the score

**1. σ no longer collapses toward certainty as houses are added.** The defect
that motivated the whole exercise:

| houses | 1 | 2 | 4 | 10 | 100 |
|---|---|---|---|---|---|
| current | 4.01pp | 2.83pp | 2.00pp | 1.27pp | **0.40pp** |
| two-term | 4.64pp | 4.27pp | 4.07pp | 3.94pp | **3.86pp** |

The old form said that with enough pollsters a poll becomes almost certain. The
new one floors at the industry-common term, which is what Jackman, Shirani-Mehr
and The Economist's production code all describe. **Today, with one house, this
changes almost nothing. The day a second house appears it changes a great deal**
— and that day is the one the plan is actively trying to bring about.

**2. The cap's effect is now produced by the arithmetic instead of imposed.**

| | σ | raw weight | cap | used |
|---|---|---|---|---|
| current, DA | 4.01pp | 0.558 | 0.500 | **0.500** (truncated) |
| two-term, DA | 4.64pp | 0.484 | — | **0.484** (arithmetic) |

The cap was approximately right in *effect* and wrong in *mechanism*: it pinned
the weight at exactly 0.500 regardless of the evidence. The sourced σ lands at
0.484 on its own and **can now move when the evidence moves.**

**3. The live 2026 forecast barely notices.** DA 79 → 78, ANC 63 → 64, ASA
24 → 25; one seat each and the intervals shift a point or two.

### A correction I owe on the map figures

The cartogram work re-measured the distortion table I put in
`PUBLISHING-BACKLOG.md` §7 and found **I had used bounding boxes, not polygon
areas.** A bounding box is not what is drawn. The polygon truth is ANC 30.1%,
DA 61.9%, MK 1.2%, PA 5.2% against my 30.6 / 61.7 / 1.4 / 4.7, and I omitted EFF
and IFP entirely — 1.5% of the ink. The DA is over-drawn slightly *more* than I
said and MK under-drawn slightly more. **The conclusion survives and the
arithmetic did not**; §7 is corrected in place and the cartogram's own test now
recomputes the table from the emitted SVG rather than from any layout object.

### The honest verdict

**Three city-years, one house and one cycle cannot establish that these constants
are right, and §1.87 said so before the run.** What this measurement shows is
that the replacement is *not worse* on the panel and is marginally better
calibrated where it acts.

The case for adopting it is therefore **not** predictive. It is that

* the old form divides a component that the literature says never shrinks;
* its central constant was a residual of the same nine readings that are the only
  metro-poll test cases the backtest has — circular by construction;
* its recency half-life is four times the longest documented value;
* and its safeguard moved the answer by 0.023 while being credited with the
  protection.

Every one of those is fixed, and every replacement constant is sourced. **That is
a Key 3 argument, and the amended bar exists precisely so that a change like this
can ship on it** — provided it does not cost accuracy, and it does not.

**Recommendation: adopt**, and flip `SIGMA_TWO_TERM` to the default. Left off in
this commit so the owner decides; nothing in the tree moves until he does.

### Recorded so it is not claimed later

The three retired constants are not *disproved*. `POLL_HOUSE_SD = 2.50pp` may
well be closer to the truth for SRF in 2026 than the sourced 1.5 + 1.5 split. The
argument is about **identifiability**, not about which number is nearer: a
residual of one house cannot be checked, and a citation can.


## 1.89 Two publishing guards that could not fire: a free token fed by a dead model, and a build that never reached the audits (2026-08-24)

Two defects, found by separate audits, with the same shape: **a check existed,
was correct, and was structurally incapable of firing.**

### A. `mode = "free"` is not a freshness guarantee

`content/joburg/stats.toml` carries

    [anc_entitlement]
    mode = "free"
    source = "regime:cap:parties.ANC.median"

used twice on the live front page. `stats.load_context` resolves a `regime:`
source by globbing `data/processed/regime_*_summary.json`. Those files were
dated **2026-08-07**. Measured on the tree at 2026-08-24, `regime_cap_summary.json`'s
scenario block still named **thirteen levers `run_model` no longer has**:

    alpha_anc, alpha_da, anc_bloc_shift, bloc_leak, da_bloc_shift, f_other,
    pa_contestation_uplift, poll_id, poll_weight, polling_lean, polling_span,
    turnout_tilt_anc, turnout_tilt_da

`forecast_summary.json` on the same tree was dated 2026-08-23 — **sixteen days
newer**. Every build for sixteen days republished a dead model's entitlement
figure onto the front page, and the drift audit reported no drift throughout.
It was right to: a fixed token cannot drift *because it is pinned*, and a free
token backed by a frozen file cannot drift *because the file is frozen*. The
one mechanism that could have caught this was structurally incapable of it, and
`mode = "free"` was doing the reassuring.

**The general rule, which nobody had stated:** a free token is only as current
as the FILE its source names. `model:` and `derived:` are safe by accident —
they read the reference run and its own draws. `regime:` is not, because
`overhang_regimes.py` is opt-in and therefore lags. Any future file-backed
source prefix inherits the same hazard.

**The fix** is `stats.freshness_problems`, wired into `build_site.main` as a
**refusal**, with `--allow-stale-sources` to stage the repair. Two signals, and
they are deliberately unequal:

* **strong — the artefact's own scenario block.** Scalar keys present in the
  file but absent from *both* `montecarlo.DEFAULTS` and the reference run's
  scenario. This identifies the model that wrote the file from what the file
  says about itself, and would survive every mtime on the disk being destroyed.
  Comparing against `DEFAULTS` alone flags the reference itself — `arrival_group`
  is recorded by a run and was never a lever — which is why the reference's own
  keys are part of "current".
* **weak — mtime**, more than `FRESHNESS_GRACE_S` = 300s behind
  `forecast_summary.json`. mtime is a property of the filesystem, not of the
  model: `cp -p`, a restore, a checkout or a `touch` all move it or fail to,
  and it says nothing about which code ran. **It is used only because there is
  nothing better on disk** — `forecast_summary.json` carries
  `_pools_artefact_key`, `_pools_stale` and `_constants_read` but no run time,
  no city, no target year and no code hash. **What would be better:** a
  `_generated` stamp written by `montecarlo` alongside the artefact key, so
  every derived file could be dated against the run rather than against the
  disk. Not done here — it changes the artefact and needs a model run.

**Refuse or warn? Refuse — and this repository has already run that
experiment.** `orphaned_scenario_claims` PRINTED its finding, and ten front-page
claims pinned to `turnout_tilt_da` survived two independent reviews that both
named them, because a print is a comment and not an audit (`build_site.py` says
so in its own margin). This defect is the same class in a better disguise: the
orphans at least declared themselves `fixed`.

`overhang_regimes.py` now `os.utime`s its six outputs after the reference run
is restored. It writes them *before* that run, so on a perfectly correct
pipeline every regime copy lags the reference by one Monte Carlo and the mtime
test would have fired on a clean build every time. **A check that cries wolf on
day one is a check somebody switches off.**

### B. `build_all.py` could not reach `build_site` or `build_portal`

`src/build_interactive.py` raises `SystemExit` at module level, deliberately and
correctly: the interactive page's in-browser drawer is the old two-bloc engine
and has not been ported to voter pools, so it refuses rather than publish
arithmetic that disagrees with the model. `build_all.py` ran it as a **mandatory**
step, and its `run()` helper raised on any non-zero exit. Step order was

    export_interactive → render_map → render_sheet → build_interactive
                                                    → build_site → build_portal

so `build_site` and `build_portal` were **unreachable through `build_all.py`, on
every city, always**. With them, every stat-provenance guard that only
`build_site.py` runs: `stats.audit` (a figure typed into prose),
`orphaned_scenario_claims`, and now `freshness_problems`. The documented
one-command build never reached a single one; they fired only when a human typed
`build_site.py` by hand.

Note the interaction. Defect B is why defect A could sit on the front page: the
one path that audits the site was the path nobody could run.

**The fix.** The step list is now a function (`build_all.plan`) so it can be
asserted without running anything, steps carry an `optional` flag, and the two
interactive steps are opt-in (`--interactive`), non-fatal, and **last** — opt-in
because they are disabled by design, non-fatal so re-enabling them cannot take
the site down again, last so that a failure mode this script does not model
still leaves a built site behind. A REQUIRED step's failure still stops the
build, and a test holds that too.

### Guards

* `tests/test_stat_freshness.py` — 8 tests. Both signals held apart; the
  reference run not mistaken for a stale file; nested blocks not counted as
  levers; the pipeline-ordering lag not reported as staleness; the message
  naming the file, both dates, the tokens and the remedy; and that `build_site`
  **refuses** rather than warns.
* `tests/test_build_all.py` — 5 tests. `build_site` and `build_portal` are
  reached when an optional step exits 1; the interactive steps are optional and
  last; they are off by default; a required failure still stops the build and
  does not reach the site.

### Not verified here, and it needs a model run

**The stale artefacts have not been regenerated.** Another worker owned the
measurement while this was written, so `overhang_regimes.py` was not run. The
consequence is concrete and the owner should expect it: **`build_site.py` now
exits 1 on this tree**, naming `regime_cap_summary.json`. That is the guard
working. Clearing it means

    .venv/bin/python src/overhang_regimes.py     # ~4 Monte Carlo runs

which also re-stamps the six regime artefacts. Until then `--allow-stale-sources`
publishes anyway and says so. The `os.utime` re-stamping and the freshness
refusal have been tested on synthetic fixtures but never against a real
`overhang_regimes.py` run.


## 1.90 The map contradicted the forecast by 1.6x, and the published distortion table measured the wrong thing (2026-08-24)

The owner's observation (PUBLISHING-BACKLOG §7) was that the geographic ward
choropleth makes the DA look dominant. It is right, it is measurable, and the
measurement is worse than the backlog recorded.

### The defect

Johannesburg's wards are drawn to hold roughly equal population and each returns
exactly one councillor, so **ward area carries no information at all**. It is
nevertheless what the eye reads first, and ward areas are wildly unequal in a way
that correlates with party: the DA's wards are large, low-density and northern,
the ANC's and MK's are small and dense. Measured on the committed
`ward_paths.json` and `ward_winner_probs.csv` (135 wards), taking each ward's
**polygon area in the projected screen coordinates the map actually draws**:

| party | wards | seat % | ink % | distortion |
|---|---|---|---|---|
| ANC | 66 | 48.9 | 30.1 | 0.62x |
| DA | 51 | 37.8 | **61.9** | **1.64x** |
| MK | 10 | 7.4 | 1.2 | **0.16x** |
| PA | 6 | 4.4 | 5.2 | 1.17x |
| EFF | 1 | 0.7 | 0.3 | 0.43x |
| IFP | 1 | 0.7 | 1.3 | 1.78x |

So the picture gives the DA nearly two-thirds of the visual field while the
forecast has it second on seats, and gives MK a sixth of what it won.

### The published table measured bounding boxes, not ink

**PUBLISHING-BACKLOG §7's table is 30.6 / 61.7 / 1.4 / 4.7, and those are the
numbers you get from each ward's BOUNDING BOX, not its polygon** — reproduced to
the decimal, all four, so this is identification and not coincidence. A bounding
box is not what is drawn. The polygon figures are 30.1 / 61.9 / 1.2 / 5.2: the
DA is over-drawn slightly *more* than stated and MK under-drawn slightly *more*,
so the correction goes against the convenient direction. The backlog's table also
omits EFF and IFP, whose two wards are 1.5% of the ink. The headline conclusion
survives unchanged; the arithmetic behind it did not, and it was going to be
published. §7 has been corrected in place with a note.

### What was built

`src/hex_cartogram.py` — one equal hexagon per ward, placed near the ward's real
centroid. Ink share then equals seat share **by construction**, and the
measurement above run over the emitted hexagons returns 1.00x for all six
parties to within 1e-9.

* **Centroids** come from the SVG paths in `data/processed/ward_paths.json`,
  which are already projected, rotated and scaled exactly as the geographic map
  draws them. That grammar is only `M`/`L`/`Z` absolute, so it parses without a
  geometry library and the cartogram needs no model run and no new data.
* **Tile size is not free.** The circumradius is set so 135 hexagons have the
  same total area as the city itself, which puts the cartogram on the
  geographic map's own footprint. Screenshotted side by side the two register:
  Diepsloot, Roodepoort, Randburg, Sandton, Soweto, Lenasia and Orange Farm all
  land on their real positions, which is what makes a toggle between the two
  legible rather than a jump-cut.
* **Assignment is optimal, not greedy.** Minimum total squared displacement over
  a rectangular linear assignment problem, solved with a numpy
  Jonker-Volgenant/Hungarian written out in `assign_optimal` because scipy is
  not a dependency here and adding one for a presentation feature is not a trade
  worth making. Measured against the greedy pass the backlog allowed
  (outermost ward first, nearest free cell):

  | | mean displacement | median | max |
  |---|---|---|---|
  | greedy | 59.4px | 36.2px | 215.3px |
  | **optimal** | **36.2px** | **33.7px** | **92.6px** |

  A 1.6x improvement on the mean and 2.3x on the worst ward, for ~0.2s. The
  greedy version's worst ward ends up 8.8 hex radii from its true centroid,
  which is not a map. Both are kept and both are deterministic; `--assign
  greedy` selects the loser. Runtime for the whole build is 0.4s.
* **Same visual language.** The four confidence tiers, the party colours, the
  challenger-coloured hatch patterns, the district labels and the tooltip text
  are the geographic map's. The colours are *imported* from `render_map`; the
  tiers cannot be (they are inline in that module's `main`), so
  `test_the_two_maps_agree_on_the_confidence_tiers` reads `render_map.py`'s
  source and fails if they drift. Independent evidence that they agree: both
  maps report the same tier counts, 49 safe / 39 strongly leaning / 23 leaning /
  24 toss-up.

### Two things found on the way

**A rounding argument was standing in for the claim.** The first renderer
emitted 135 separate `<polygon>`s with coordinates rounded to one decimal for
legibility, which made the tiles differ in area by ~1e-2 px^2 — and
`test_every_hexagon_is_identical_and_none_overlap` failed on it. Tiny, invisible,
and exactly the wrong shape of defect: the entire claim of the figure is that
every ward is drawn the same size, so that must be true by construction and not
true to a tolerance. The tiles are now `<use>` references to one shared
`#hexcell` polygon. The test measures the emitted markup rather than the layout
object, and also refuses a `transform` on any tile, which is the other way a
`<use>` could be rescaled.

**MK is missing from the published map's party key.** `render_map.py`'s swatch
list is `("ANC", "DA", "EFF", "ASA", "PA", "IFP", "ALJAMAAH")` — MK is not in it,
wins 10 wards in this forecast, and has nowhere on the page to be looked up. The
cartogram's key includes it. `render_map.py` was NOT edited: it cannot be re-run
without rewriting `forecast-sheet.html`, which another worker owns this session.
One line, for whoever holds that file next.

### What is not verified

The tooltip JS is checked only for its content, not its behaviour — nothing here
drives a browser event. The figure was screenshotted headless at 1100px wide and
read; it has not been seen on a phone. And the cartogram is **not wired into any
page**: `--into` will splice it at `__HEXMAP_START__`/`__HEXMAP_END__`, and no
page carries those markers yet.


---

## 1.91 The two-term σ adopted; and the arrivals conversion fails on the opposite population to the one suspected (2026-08-24)

### Adopted

`SIGMA_TWO_TERM` is the default on the owner's decision, on §1.88's measurement.
`SIGMA_TWO_TERM=0` runs the retired four-component form for comparison.

Panel on the settled tree: **384 coherent, CRPS 329.2** against 384 / 329.4. The
golden is re-recorded with its reason in the file, per `CLAUDE.md`.

It ships on **identifiability, not accuracy** — the panel could not tell the two
apart, and §1.87 said in advance that it could not. What changed is that σ no
longer collapses toward certainty as houses are added, and the DA's blend weight
is 0.484 by arithmetic rather than 0.500 pinned by a cap.

### The arrivals question, and the answer inverts the intuition

The owner asked about the rule that *"looks at national results and tries to
shoehorn them locally"*, expecting it to fail because **many small arrivals are
hyper-local**. The mechanism does fail. **It fails on the opposite population.**

`polling.metro_estimate` divides a party's national share by the share of the
national roll held by the municipalities it contests. For a party standing in
**one** metro, that denominator *is* that metro — so the conversion is **exact by
identity**. Measured over every arrival in the eight-metro archive:

| | arrivals | single-metro | multi-metro median \|log ratio\| |
|---|---|---|---|
| 2016 | 83 | 46 (55%) | **0.234** |
| 2021 | 175 | 67 (38%) | **0.431** |

0.431 in log units is a factor of **1.54**. So the hyper-local arrivals — the
majority at 2016 — are handled exactly right, and the error lives entirely in the
**widely-contesting** parties.

**Which is worse than the intuition, not better**, because the case the whole
path was built for is ActionSA — a multi-metro party. Its 9.78% by this route sat
against actual metro shares of **18.12, 9.28, 7.36 and 2.35**. The function's own
docstring concedes this; the model applies the number anyway, **with no per-metro
differentiation of any kind**, because `scenario["poll_levels"][party]` is one
scalar per party.

So §1.65's 48 coherent seats are earned by a mechanism that is exact where it is
trivial and out by half where it does the work.

### And a correction to my own claim about task A3

I reported that adding a national 2026 poll would re-enable the 48-seat arrivals
channel. **That is wrong.** The channel is blocked at 2026 by **two independent
gates**, and the poll is only one of them:

    contesting_parties(joburg, 2016) -> 28 parties
    contesting_parties(joburg, 2021) -> 57 parties
    contesting_parties(joburg, 2026) ->  0 parties

The loop reads `if _party not in (_roster or set()): continue`, so an empty
roster skips **every** party. The roster is the nomination fact, and **nomination
lists do not exist until 16 September 2026.**

**The arrivals channel therefore cannot fire before 16 September no matter what
poll is acquired.** `PLAN-TO-LIVE.md`'s A3 is corrected: acquiring a national
poll is necessary and not sufficient, and its benefit is dated to the lists
landing, not to the acquisition.

### What was researched and never built

The owner asked whether the earlier work on party events had been built into the
model. **It was not, and the record should say so plainly.**

§1.71–§1.73 established the mechanism and imported Powell & Tucker's Type A / Type
B distinction. §1.74 pre-registered a documented-event register and measured it:
**refuted**, both conditions missed. §1.78 re-measured it on the restored tree —
it improves seats (384 → 360) but still fails the pre-registered bar. §1.82 then
showed it and the footprint exclusion are competing descriptions of one defect.

§1.74's own conclusion was *"route, do not drop"* — an exclusion moves the
volatility out of the model's prior and into its error, and it measured that
happening. **The routing has never been built.** It is task #37.

And the arrivals **sizing** — the contested-area conversion, the reach-weighted
split, the comparator window — has never been rebuilt on external evidence at
all, unlike the polling layer, which was. The owner's position is that the
existing method was a best guess and gets no special treatment. That is correct
and it is now commissioned: a search of how forecasters in other systems size new
parties, splits, mergers and leadership shocks, on the same terms as the polling
search that overturned §1.67's structure.


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

## 1.92 The test helper that measured a model we do not run, and the ceiling that replaced a chosen cap (2026-08-24)

**Adopting the two-term σ (§1.91) left four suite failures. Two were the
adoption doing its job. One was a helper that had quietly stopped mirroring the
model. The fourth was a question asked wrongly — by me — and the answer is worth
recording because it looked like a serious regression for an hour.**

### The helper

`tests/test_polling_synthetic.py::_weight` re-implements the model's poll-blend
decision: σ → `blend_weight` → cap. When `SIGMA_TWO_TERM` became the default the
model stopped applying `weight_cap`; the helper did not. **Every test in that
module was therefore measuring a hybrid the model has never run — the NEW σ
against the OLD cap.** One house pinned at exactly 0.500 from one wave to a
hundred, which reads as the cap working correctly and was the helper disagreeing
with the code.

The docstring on `_recency_weights` had already named this exact hazard —
*"two copies of one calculation is this repository's most reliable defect"* —
about a different pair of functions, in this same module.

### The question I asked wrongly

With the helper fixed, the guarantee looked broken:

    100 waves of ONE house   -> 0.5755
      2 waves, TWO houses    -> 0.5652
    volume beats replication? YES — BAD

That is a hundred polls against two. It measures fieldwork quantity, not
replication. **Hold volume constant and replication wins at every level:**

    polls    1 house   2 houses   4 houses
        4     0.5617     0.5798     0.5893
       20     0.5732     0.5920     0.6019
      100     0.5755     0.5945     0.6045

### The bound that replaced the cap, and why it is better than the cap

The real question is whether a single house can buy the forecast by publishing
weekly. It cannot, and **the bound is now structural rather than chosen.**
`SIGMA_COMMON` is never divided by `h_eff`, so a lone house's weight saturates:

    waves      1        2        5       20      100    1,000   10,000
    weight  0.5226   0.5480   0.5645   0.5732   0.5755  0.5760  0.5761

Ten thousand waves buy no more than a thousand. **Two houses pass that ceiling
with four polls** (0.5798). The retired `weight_cap` imposed a ceiling by
truncation; the decomposition produces one by consequence.

So the bound is now derived and named rather than restated:

* `polling._sigma_total(sampling_sq, h_eff, screen, drift)` — the two-term total
  in ONE place.
* `polling.sigma_floor(polls, party, share)` — `aggregate_sd` with
  `include_sampling=False`. **The same code path**, so the floor and the thing
  it bounds cannot drift apart.
* `polling.house_ceiling(...)` — `blend_weight` of that floor.

Three tests that each restated `weight_cap(1.0)` now assert against
`house_ceiling`, and the floor test's hand-typed `0.03` and `0.015` are gone in
favour of `sigma_floor`. The ceiling is tight: the flood sits exactly on it
(0.5761) and a million-respondent single poll just under (0.57606).

### The screen term, kept as a policy and labelled as one

§1.87 folded the screen surcharge into the common term on the argument that a
decomposition cannot identify its own components (Dominitz & Manski 2025). That
argument is sound and it silently deleted the only cost this model imposes for
hiding a likely-voter screen — a disclosed and an undisclosed poll priced
identically at 0.0381. A test caught it.

It is restored, **relabelled honestly**: not a measurement of the excess error
of an undisclosed screen, but a declared surcharge for opacity, not divided by
`h_eff` because opacity is not averaged away by more houses. It is defensible
where the other three components were not precisely because it does not pretend
to be measured — a house can remove it at any time by publishing its screen.

## 1.93 Duplicated logic: a repository-wide audit, and the rule it establishes (2026-08-24)

**§1.92's helper was not an isolated slip, and the owner said so: detailed logic
must not live in two places.** Three read-only audits were run over `src/`,
`tests/`, and the code/config/docs/site boundary. The full inventory is
`DUPLICATION-AUDIT.md`; this entry records what it establishes.

### The rule

A second copy is permitted **only** where its independence is the point — `fold.py`
validating the deterministic core, `test_hex_cartogram.py` restating the
closed-form hexagon identities. Every such copy says so in its docstring.
Everything else imports.

### One negative result, and it matters

Every module-level numeric constant and all 33 `DEFAULTS` keys were
cross-checked against every number quoted beside them in the nine standing
documents. **Every restated value matches.** `SHRINK`, `SPINE_K`,
`RELIABILITY_HALF`, `SD_FLOOR`/`SD_CEILING`, `SPLIT_SD_FLOOR`,
`SPLINTER_PARENT_WEIGHT`, `TURNOUT_CORRELATION`, `LEVEL_DF`, the `ALPHA_*` four,
`REFERENCE_SHARE`/`SLATE`, `CLAIM_FRACTION`, `DIRICHLET_FLOOR` — all agree.

**The registers are not where the drift is.** The drift is in restated
*mechanisms*, restated *rules*, and typed *outputs*. That is worth knowing
because the register discipline is expensive and it is working.

### The clearest case: one rule, two copies, and the strict one is not the
documented one

`polling.screen` guards with `scope == "metro" and not city` — an exact string
match. The register holds `ipsos-w2-2025-metros` at `scope: "metro-aggregate"`
with no `city`, whose own note says using it as a city poll *"would import Cape
Town's DA and eThekwini's MK into Johannesburg"*. It passes `screen`, and
`aggregate` blends it: DA −3.18pp, ANC +2.65pp, **PA conjured at 4.00% and IFP
at 2.00%** in Johannesburg, `H_eff` 1.464 against 1.0.

**It does not reach the forecast**, because `montecarlo:2876` re-states the rule
inline and its version is strict. That is the finding, not a reprieve: the layer
documenting itself as *"Admitted polls, and every exclusion WITH ITS REASON"* is
wrong, and the forecast is saved by a copy of the rule in another module.
`test_polling_register` asserts `usable_for` and `screen` agree with each other;
nothing asserted either agrees with what the model uses.

### Already wrong, currently inert

* `montecarlo:2513-2516` applies the by-election decay **twice** — `decay²` over
  a denominator of `decay` — while the comment above it states the opposite
  invariant and claims parity with `byelections.py`. Inert only because
  `w_bye_local_*` ship at 0.0, and `:170-171` names 0.75/0.35 as "the value
  tested".
* `fold.py:682,700` call `seats.allocate` without `total_seats`, so **every city
  is allocated a 270-seat Johannesburg council**.
* `PERTURB` sets `turnout_correlation` twice (0.0 with its explanation, then
  −0.9). Python keeps the last; the documented perturbation has never run. It is
  the only duplicate key in either file, by AST walk.
* `pools._npe_citywide_for` is a character-identical copy of `levels._citywide`
  **without** the §1.75 refusal, still returning `{}` for a missing file — the
  hole §1.75 was written to close, still open one module over.

### Wrong and live

`polling.aggregate` does not call `_recency_weights`, the helper factored out
*"so the aggregate and `effective_houses` cannot weight the same polls
differently"*. It re-derives the decay inline and differs three ways: the date
parser raises where the helper returns `None`, an undated poll is dropped here
and weighted 0 there, and `asof` defaults over different sets. **The centre is
the path that moves the published number.**

### On the shipping gate

The θ estimator is written four times — `levels.theta_prior:718-729`,
`levels._shrunk:819-830`, `theta_residual.form_b` and `form_c`. The amended bar
makes the held-out NLL an untradeable floor, and that floor is computed from
forms whose own docstring admits they use a different size argument than
`theta_prior` passes. **A change to `levels.py` moves the model and leaves the
gate where it was.** Separately, `theta_prior` falls back to the size centre and
`_shrunk` to the flat centre, which `theta_prior`'s own comment calls the wrong
one — and the spine takes `_shrunk`'s. The named case is MK in 2026.

### The record I failed to change in the same commit

§1.91 adopted `SIGMA_TWO_TERM` and did not touch the registers that describe it.
`JUDGEMENT-CALLS.md:348` still said *"pre-registered and OFF by default"*; four
further rows described the retired σ, the cap that no longer binds, and
`POLL_HOUSE_SD` as the live house term. `MACHINERY.md:284` gave the channel as
`σ_poll = 3.03pp` with no cap. `montecarlo` contradicted itself twenty lines
apart. **This is `CLAUDE.md`'s own non-negotiable, missed on the most contested
lever in the model, by the author of the change, on the day of the change.**

### The guard that made another guard vacuous, and said so

Replacing every literal fallback broke
`test_every_literal_fallback_equals_the_declared_default` — **by finding none
left to check.** It failed on its own self-check:

> no `scenario.get(key, <literal>)` calls found at all — either the pattern
> changed or this test has stopped looking, and it would then pass forever
> while checking nothing

That assertion was added because a test that silently stops looking is worse
than one that fails, and it earned itself here. An equality check over a set
that is empty by construction is not a guarantee.

So the guarantee **moved rather than being deleted**. The structural guard
refuses new literals outright; the equality test was repurposed to the risk that
survives — a fallback that is a NAMED CONSTANT, which is the good pattern and is
still two objects. `montecarlo` had an import-time assert linking exactly one of
the six poll constants to its `DEFAULTS` entry; the other five were unlinked.
`test_every_named_fallback_resolves_to_the_declared_default` is that assert
generalised over `src/`, with no allowlist and the same self-check.

### `poll_house_k` is now inert, and is declared rather than deleted

The lever set the cap `H_eff/(H_eff+k)`; the cap is gone, so nothing reads it on
the shipped path and `test_every_tunable_lever_actually_moves_the_forecast`
correctly reported it dead at 2026. It is **not** deleted, because the retired σ
is still reachable at `SIGMA_TWO_TERM=0` for A/B and reads it there. It is in
`EXPECTED_INERT` with that reason, and struck through in `JUDGEMENT-CALLS.md`.
§1.68 deleted `POLL_K` outright when its path went; the difference is that that
path was removed and this one is retained as an escape hatch.

### The de-duplication is number-neutral, and the panel movement is the screen term

**Claiming a refactor moved nothing is worthless unless it is measured, and the
first measurement said the opposite.** The settled tree scored 382 coherent
against the committed 384, so either the extractions had moved the model or the
committed artefact was taken at a different draw count — and `history.json`
records neither its draws nor its seed, so the artefact could not answer.
(Logged against task #28: `forecast_summary.json` carries
`_pools_artefact_key`, `_pools_stale` and `_constants_read`; the panel artefact
carries no provenance at all.)

Resolved by running the ORIGINAL source at the same draws, which needed
`SIGMA_TWO_TERM=1` in the environment because the switch is off at `HEAD`.
Three runs, 1500 draws, sixteen city-years:

| tree | coherent | CRPS | seat abs |
|---|---|---|---|
| `HEAD` + `SIGMA_TWO_TERM=1` | **384** | **329.2** | **410** |
| de-duplicated, screen term removed | **384** | **329.2** | **410** |
| de-duplicated, screen term restored | 382 | 329.0 | 407 |

**So every extraction in §1.93 is number-neutral to the seat** — `_sigma_total`,
`sigma_floor`, the `screen` city rule and `metro_polls`/`national_polls`, and
all fourteen literal-to-`DEFAULTS` replacements. The middle row is the proof:
identical code to the third, one term removed, and it lands on the baseline
exactly.

**The entire movement is the screen surcharge restored in §1.92**, and it moves
all three measures in the right direction. It is NOT reported as an improvement:
draw noise on coherent seats is ±2 (§1.31), so two seats is inside it. The
surcharge is kept on the argument in §1.92 — that a model must charge something
for an undisclosed likely-voter screen — and the measurement's only claim is
that doing so costs nothing.

A first attempt at this comparison was invalid and is recorded because the
mistake is easy to repeat: the baseline capture was run WITHOUT the environment
switch, so it took the retired four-component branch and reported a σ of
0.040645 where the two-term form gives 0.034015. **A/B against a default that
the working tree has changed must set the switch explicitly on both sides.**

**Run-to-run reproducibility, measured.** Two runs of identical code on the
settled tree agree to **1.9e-14** across every scalar metric, and no seat metric
moves at all. That is the parallel float-summation variation §1.46 documented
between serial and parallel; the panel is reproducible to the seat, which is the
resolution any claim here is made at.

`ITERATING.md` rule 8's two tables were re-pasted from the settled run —
ranks 4-12 n 58 → 57, and the vote-error table to +12.38 / 93.38, −26.29 /
72.54, +4.42 / 22.45, phantom 9.49pp.

## 1.94 The two levers that carry the model, re-read on sixteen: one grew, one reversed (2026-08-25)

**§1.70 left a standing instruction and it was never discharged:** *"Every
number in this repository predating this entry was measured on nine city-years
and must be re-read on sixteen before it is quoted again."* Two numbers matter
more than all the others put together. `level_shrink` was measured at **48
coherent seats** (§1.44) and the poll channel at **48** (§1.65); against a
122-seat margin over uniform swing they are about **79% of everything the model
has ever been shown to be worth**. Both were still being quoted from the nine as
recently as §1.91, yesterday.

They have now been re-read. **One grew. One reversed.**

Method, and it is Key 1's, not a bootstrap: paired per-city-year differences on
identical seeds against the committed baseline (382 coherent / 329.0 CRPS / 407
seat_abs, 1500 draws, commit `2742785`), reported as sign count and sum **split
by cycle**. `ITERATING.md` Key 1 forbids a p-value from the eight metros inside
a cycle — they share one national swing, so both the binomial and the metro
bootstrap are anti-conservative.

### `level_shrink` — survives, and grows: +52

| | sum | better | worse | tied |
|---|---|---|---|---|
| 2016 seats | **+2** | 1 | 2 | **5** |
| 2021 seats | **+50** | 6 | 1 | 1 |
| 2016 CRPS | +9.65 | | | |
| 2021 CRPS | +30.29 | | | |

**Total worth +52 coherent seats**, against 48 claimed on the nine. Key 1's
three conditions all hold: same sign in both cycles, no cycle shows a net loss,
and 6 of 8 strictly better in 2021.

**But it is a 2021 effect, and the honest statement of it says so.** +50 in
2021 against **+2 in 2016**, where five of eight city-years are exactly tied and
two are worse. "+2 with five ties" passes the letter of the replication
condition and is noise around zero on any reading. The lever is confirmed as
large and not-harmful; it is *not* confirmed as general.

That is mechanistically coherent rather than troubling. The shrink compresses
levels, and 2021 is the fragmented cycle — ActionSA's arrival — while 2016 is
not. **It is the first direct evidence for task A3 (`make level_shrink
fragmentation-dependent`), which until now was an unsupported guess.**

### The poll channel — does not replicate: −6

| | sum | better | worse | tied |
|---|---|---|---|---|
| 2016 seats | **−4** | 0 | 2 | 6 |
| 2021 seats | **−2** | 1 | 2 | 5 |
| 2016 CRPS | −1.40 | | | |
| 2021 CRPS | −3.00 | | | |

**Turning the poll channel off makes the model better by 6 coherent seats and
4.4 CRPS.** It fails two of Key 1's three conditions. The +48 does not
replicate; it inverts.

**The three-way decomposition is monotone, and monotone the wrong way** — the
same three configurations §1.65 measured, sixteen city-years, 1500 draws:

| `poll_paths` | coherent | CRPS | | §1.65, nine city-years |
|---|---|---|---|---|
| `off` | **376** | **324.6** | | 304 / 263.7 |
| `arrivals` | 378 | 327.6 | | 256 / 232.7 |
| `all` (shipped) | 382 | 329.0 | | 254 / 232.9 |

Each path costs on its own. The **metro** path is worth **−4** seats and −1.4
CRPS, all of it in 2016 — in 2021 all eight city-years are exactly tied, which
is correct, because the register holds no metro poll declared for 2021. The
**arrivals** path is worth **−2** seats and −3.0 CRPS.

**The gate was open — this is a measurement, not a null measured with the gate
shut.** That check is mandatory here because §1.68 was burned by exactly it
(`_LEGACY_POLL`: *"That null was measured WITH THE GATE SHUT"*). Verified: a
national poll is admitted at every one of the sixteen city-years and
`contesting_parties` returns a roster of 16–57 parties at each. The path runs.

**And the tie pattern is fully explained, which is what makes the measurement
trustworthy.** The arrivals path acts only on a party in the national poll that
has **no baseline**. In the 2016 cycle the national poll carries ANC, DA and EFF
and all three have baselines everywhere — **so the arrivals path cannot fire at
all in 2016**, and the two non-ties there are the metro path at Johannesburg and
Tshwane. In 2021 it fires on ActionSA, in the four metros where ASA is on the
roster. Eleven ties, every one accounted for.

### It is not the panel — the control settles it

Restricted to **§1.65's own nine city-years**, the same measurement gives **−4**,
not +50:

| city-year | §1.65 off/all | worth | now off/all | worth |
|---|---|---|---|---|
| Johannesburg 2016 | 18 / 16 | +2 | 20 / 22 | **−2** |
| Johannesburg 2021 | 90 / 86 | +4 | 86 / 90 | **−4** |
| **Tshwane 2021** | 52 / 30 | **+22** | 34 / 34 | **0** |
| **Ekurhuleni 2021** | 38 / 18 | **+20** | 28 / 22 | +6 |
| eThekwini 2021 | 34 / 32 | +2 | 32 / 36 | **−4** |
| Cape Town 2021 | 34 / 34 | 0 | 36 / 36 | 0 |
| Mangaung 2021 | 10 / 10 | 0 | 10 / 10 | 0 |
| Nelson Mandela Bay 2021 | 18 / 18 | 0 | 18 / 18 | 0 |
| Buffalo City 2021 | 10 / 10 | 0 | 12 / 12 | 0 |
| **total** | | **+50** | | **−4** |

So the reversal is **not** an artefact of doubling the panel. On the identical
nine city-years the effect is gone.

### What actually happened, and it is the more useful finding

Read the two columns for the two city-years that carried §1.65's result. Tshwane
2021 and Ekurhuleni 2021 supplied **42 of the 50 seats**. In both, the model
**with** the channel got slightly *worse* (30 → 34; 18 → 22) while the model
**without** it got dramatically *better* (52 → 34; 38 → 28).

**The poll channel was worth 50 seats because it was patching a hole. The hole
has since been fixed and the patch now costs 4.** The most likely repair is
§1.75 — six verified input files restored, which moved the panel 400 → 384 and
changed the θ and ρ records for every metro — though §1.91's σ adoption and the
2016 spec emission are in the same window and this entry does not attempt to
apportion between them.

### Consequences, and none of them is optional

1. **`poll_paths` must not be quoted at 48 seats anywhere.** Every live citation
   is now wrong: `MODEL-LOG` §1.65 and §1.91, `JUDGEMENT-CALLS.md` §A, and the
   memory note `live-forecast-is-not-the-backtested-model`.
2. **The "two 48s carry 79% of the margin" framing is dead.** One of the two is
   worth −6. The model's measured performance now rests on `level_shrink`, and
   mostly in one cycle.
3. **This does not by itself mean switch the channel off at 2026** — and the
   reason is uncomfortable. §1.65's own §A row records that the 2026 forecast
   depends on the metro path for its headline, and the backtest cannot score the
   2026 configuration at all. But a channel that is worth −6 where it *can* be
   scored has lost the argument that justified keeping it live where it cannot.
   That is a decision for the owner, pre-registered before it is taken.
4. **It vindicates the standing instruction.** §1.70 said every nine-city-year
   number must be re-read before being quoted. Had that been done when it was
   written, this would have been found four days ago instead of being quoted
   twice more in the interim.

## 1.95 How much do you believe the polls? A dial, and it decides the headline (2026-08-25)

**§1.94 measured the poll channel at −6 coherent seats and the obvious reading
was "switch it off". That reading is wrong, and the owner said so:**

> we need to incorporate polls as they come in and let users 'believe them' to a
> more or lesser extent in the interactive. But they are a major check that we
> are in the ballpark.

**Polls do three jobs here and the backtest scores one of them.**

1. a forecast **input** — scored, currently −6 (§1.94);
2. an **external check** that the model is in the ballpark — the only
   independent reading of this election that exists, and **unscoreable by
   construction**, because a backtest can only compare the model against
   results, never against a second opinion;
3. a **reader-facing** exploration.

A binary switch cannot express any of that. And −6 is evidence that the
*weighting* is wrong, not that the polls are empty.

### `poll_credence`

A lever, default **1.0**, multiplying the metro-poll blend weight `w` before it
is applied and clamped to [0, 1]. **1.0 is the identity**, so adopting it moved
no number — verified against `forecast_frozen.json`: seat-draw matrix hash
identical, every party's median, p5 and p95 identical, the only difference being
the new key in the frozen scenario. That is what the freeze is for, and it is
the first change it has adjudicated.

Scoped to the **metro blend** deliberately. The arrivals path is a *route
precedence* in `blended_centres`, not a blend — for a party with no local record
there is no alternative estimate to blend against — so credence has no meaning
there, and `poll_paths` remains its switch.

### It is the largest single driver of the headline

Johannesburg 2026, 400 draws, median seats:

| | credence 0.0 | **1.0 (shipped)** | 2.0 |
|---|---|---|---|
| DA | 68 | **77** | 88 |
| ANC | 68 | **64** | 61 |
| ASA | 28 | 26 | 24 |
| EFF | 26 | 24 | 21 |

**At zero belief in the polls the race is a dead heat. At the shipped weighting
the DA leads by thirteen.** That dependence has been in the model since the
metro path shipped; what is new is that it is now a number a reader can move
rather than a consequence of σ arithmetic nobody outside this repository can
see. §1.65's own register row has said for weeks that "one house, two waves,
decides the headline" — this is that sentence made operable.

**1.0 is the incumbent, not a recommendation.** The value the backtest supports
has not been measured; the paired sweep across the panel is pre-registered and
not yet run. Quote it as unmeasured until it is.

## 1.96 The freeze was being used as a benchmark, which protects the bugs (2026-08-25)

**Corrected by the owner, within hours of the mistake being made, and it is the
second time this week that a rule already written in `CLAUDE.md` was broken by
the person who had just read it.**

`src/freeze.py` shipped on 2026-08-25 with a stated purpose of being "a fixed
reference to diff against", and the restructure plan made *"every commit must
reproduce the frozen panel to the seat or be reverted"* its verification gate.
`ARCHITECTURE.md`, three task descriptions and §1.95 all carried the same
framing.

`CLAUDE.md` has said the opposite since the repository was started:

> The published forecast is a recent output of an earlier version — **not a
> benchmark, not a target, not evidence.**

The owner's instruction, verbatim: *"do not compare work against the freeze or
published model. We are not benchmarking against broken implementations we can't
evaluate. We do everything as well as we can and back test to real elections."*

### Why it is harmful and not merely untidy

**"Reproduce the old numbers or revert" makes the current defects the definition
of correct.** This model is known to contain, right now: a by-election local
mean that applies its decay twice; a seat allocator called on every draw with no
test at all; and, until four days ago, a poll channel believed to be worth +48
that is worth **−6** (§1.94). A rule that reverts any change touching those
paths is a rule that **protects them**, and it would have done so silently,
because "the numbers match" reads as success.

Agreement with an earlier output is evidence of nothing, because **that output
was never known to be right.** The comparison feels rigorous, which is what
makes it dangerous.

### What replaces it

When a change moves a number the question is never *"does it still match?"*. It
is *"does the backtest against real election results improve?"* — on the sixteen
city-years, paired and cycle-replicated, against the four keys.

A refactor is still **expected** to be number-neutral. The difference is what
happens when it is not: **investigate, do not revert.** The freeze's role is a
tripwire that says *go and look*, plus a record of what was published and the
configuration that produced it, so the forecast can be held to its own numbers
after 4 November. Neither of those is a judgement.

The same applies to the goldens. They are not re-recorded silently — that
destroys the record of what changed — but **a golden that disagrees with a
better model is the golden that is wrong.**

### Where it is now written

`CLAUDE.md` carries it in full, under *"Nothing this model has ever produced is
a standard of correctness"*. `ITERATING.md` carries a pointer, not a copy,
because a rule written twice is a rule that drifts (§1.93). `ARCHITECTURE.md`,
`src/freeze.py`, `tests/test_freeze.py` and tasks A and C are corrected.

**§1.95's number-neutrality check on `poll_credence` stands as a fact** — the
seat-draw hash was identical and that is worth knowing — but it was not, and is
not, the reason the lever is acceptable. The reason is that 1.0 is the identity.
