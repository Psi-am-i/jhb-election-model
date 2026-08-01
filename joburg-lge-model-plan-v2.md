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
