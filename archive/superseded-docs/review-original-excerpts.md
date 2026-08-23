# Verbatim excerpts from model-review.html, for the compare page

## Verdict

The data work, the seat allocator, and the backtesting discipline are
genuinely strong — the allocator reproducing three published councils exactly
is a real credential, and several plan errors (softmax/logit,
raw-versus-calibrated θ, entrant seeding) were caught and fixed well. But the
Monte Carlo stage cut corners the plan explicitly warned against, and one of
them makes the headline published conclusion **factually wrong under the
model's own output**: a DA + EFF + MK coalition reaches a majority in 61% of
the model's own draws, yet every published document says no such coalition
exists.

## E1

Plan §3.8 was explicit: enumerate **all 2ⁿ subsets**, reduce to minimal
winning coalitions, and "keep political feasibility as a separate, toggleable
layer… There is no reason to pre-filter on plausibility, and good reason not
to." The implementation did the opposite: `montecarlo.py:60–67` hard-codes six
politically plausible coalitions and checks only those. […] So the claim in
MODEL-LOG §1.11, METHODOLOGY §5B, and the forecast sheet — *"no two- or
three-party coalition reaches 136 except ANC+DA"* — is wrong. DA+EFF+MK clears
the majority in 61% of draws. […] What happened is a conflation of "the ANC"
with "the ANC bloc" […] the plan's whole §3.8 argument (Mashaba governed on
external EFF support for three years; declared red lines have a short
half-life) was that the arithmetic layer must never inherit that judgement.

## E2 to E6

**E2** — `draw_target` centres the within-bloc Dirichlet on **2024
proportions**. But the plan's §3.5 central θ values encode deliberate
asymmetric views: θ_MK = 0.60 (no ward machinery, beaten by ActionSA in its
one Soweto test, Ipsos at 8%) […] MK's plan-central case (~7.3% citywide, ~20
seats) and its bear case are essentially unreachable.

**E3** — Plan §3.7 steps 3–5: predict ward winners, deduct from entitlement,
**check for overhang and expand the council if it occurs** — and the plan's
own §0 flags overhang as "a live risk for 2026, not a theoretical one". The
Monte Carlo allocates from combined votes and never looks at wards.

**E4** — **by-elections** (38 contests fetched), **polling**, and **census
covariates** appear nowhere in the pipeline. The forecast's citywide
distribution rests entirely on four historical NPE→LGE transitions […]
Meanwhile the sheet's colophon lists "IEC by-election results, 2021–2026" as a
source, which is not true of the numbers on the sheet.

**E5** — The sheet says: *"Tested against 2021 without being shown the
answer, the model called 128 of 135 ward winners."* […] the headline
seat-error row uses θ recalibrated against the actual 2021 citywide shares.
The genuinely blind configuration had a total seat error of **54** [later
re-scored to 60]. The internal documents are honest about this distinction;
the sheet is not.

**E6** — A single shared `f_other` draw scales the IFP, VF+, ACDP, Rise and
the rest identically per draw. This produces the implausibly tight published
intervals — Rise 5–7 seats, IFP 4–6; a party's 90% interval spanning two
seats is not credible.

## Addendum: what the corrected model says

The dominant new finding is one the broken version could not see:
**overhang is the modal outcome (89% of draws)**. The ANC wins ~73 of 135
wards on a ~65-seat entitlement, the council expands to a median of ~281, and
the majority threshold moves to ~141 — raising the bar for every coalition.
ANC+DA clears it in 86.5% of draws and is the dominant minimal winning
coalition; a DA-led minority via abstention (the 2021 pattern) is viable in
61%; the eight-party anti-ANC alliance is a coin flip at 53%; the DA is
largest in only 63% of draws once overhang seats count. Banzhaf indices
settle E1's asserted claim the other way: ActionSA (11%) out-ranks the PA
(5%) as kingmaker.

## Addendum: still open

The Schedule 1 overhang fine print has no published IEC worked example (task
#20 — now the forecast's largest legal uncertainty, bounded by the fixed-270
toggle); MK's γ cannot be fitted from one election and stays a documented
default; the Census Small Area Layer (O7) still gates a better turnout
covariate; and the citywide ranges remain judgements no backtest can
validate — which is precisely why they are now sliders.
