# Second-round maths audit — interactive/coalition engine (agent finished 2026-08-06 13:03)

All scope items are now covered. Compiling the report.

## SECOND-ROUND AUDIT — findings

### Statute implementation (scope 1)

**[MEDIUM] src/montecarlo.py:392-409 + site/dev/interactive.html deduct block — equality trigger uses strict `>`, statute item 16(1) says "equal to or greater"** — Both engines fire the excessive-seats machinery only when `ward_wins > entitlement`. Amended item 16(1) triggers at *equal to or greater*: a party whose wins exactly equal its entitlement should (on the plain reading MODEL-LOG 1.17 itself quotes — 16(3)'s B/D reference "the party with excessive seats", the 16(1) class) have its votes excluded and the quota recomputed for everyone else. Excluding an exactly-at-quota party is *not* a no-op: I brute-forced 166,505 forced-equality cases against a direct implementation of the (A−B)//(C−(D+E))+1 formula with the equal-or-greater trigger — **6,959 (4.2%) shift at least one seat between the other parties** (example: votes {P0:29200,…P5:478600}, P4 wins 79 = entitlement 79 → code gives P2 6/P5 77, statute gives P2 7/P5 76). Instrumenting the dev page's engine: **6.1% of draws (183/3000) contain a first-round wins==entitlement party**, so expected distortion ≈ 0.25% of draws moving one seat among minor parties — headline-invisible, but it is a genuine statutory-fidelity gap, and Laingsburg (3 wins > 2 entitlement) cannot arbitrate the equality case. Fix: change both engines' trigger to `>=` (guarded by `wins > 0`), or log a documented ruling that equality does not invoke 16(3). Caveat honestly: the statutory text is ambiguous on whether an exactly-equal party "has excessive seats".

**Otherwise the deduct branch is exact.** With the strict-`>` reading held fixed, the iterative `allocate(votes_minus_fixed, 270−Σfixed_wins)` reproduces (A−B)//(C−(D+E))+1 arithmetic identically — 4,000 randomized trials against a direct statutory implementation: **0 mismatches**, including double-excessive and cascade cases (batch exclusion per iteration matches 16's "repeat" structure; E=0 is right since the sim has no independents). The Laingsburg quota check reproduces: (6453−1530)//(7−3)+1 = 1231. Column sums to 270 in every trial. The equality case as the code handles it (party keeps wards, gets entitlement = wins, no recalc) is at least internally consistent.

**[LOW] src/montecarlo.py:392-394,633-634 — `over`/`overhang_count` only counts first-round excessive parties** — parties that become excessive only after a re-allocation iteration are never added to `over`, so `p_excessive_by_party` slightly undercounts cascades. Same in JS (`overhangBy` recorded before the fix-loop).

**[LOW] Python vs JS divergence in unreachable territory** — Python `allocate` raises ValueError when largest-remainder shortfall exceeds party count; JS `allocate` silently truncates via `Math.min(total-used,n)` and, in that pathological branch, could hand remainder seats to zero-vote (`rem=-1`) parties. Requires vote totals smaller than the seat count — unreachable with real tallies. Also: a zero-combined-votes party with ward wins would keep its wins in JS but get nothing in Python (filtered from `combined`); unreachable since winners always have votes.

### Draw machinery (scope 2)

**bloc_leak: arithmetically sound, JS ≡ Python.** `leak>0` adds `leak×max(0,−a_shift)` to the DA bloc *without* deducting from the ANC bloc, then renormalises — correct in vote-space terms: crossing voters (who would otherwise abstain) enlarge the cast total, so *every* other party's share deflates proportionally, including intra-ANC-bloc. `leak<0` is a sum-preserving transfer (redirected votes, no turnout change), leaving non-bloc parties untouched. The asymmetry is the right physics for the two stories told in the comments. Magnitude of non-bloc deflation at extreme settings (leak=1, a_shift=−22pts): ~18% relative — large but intentional. Side effect: the §3.5 implied-θ bounds counters will fire more often under leak≠0 (cosmetic).

**blended_centres + poll stacking: no double-count in the convexity sense.** centre = (1−wp)·[(1−wb)·mode + wb·bye_clamped] + wp·poll_clamped — weights sum to 1; the poll blend properly dilutes the bye tilt rather than stacking additively. Both clamps use identical PLAN_BOUNDS×base2024 arithmetic in both engines (verified line-by-line; JS `BOUNDS` matches `PLAN_BOUNDS` value-for-value). Residual risks, both latent: (a) `polling_lean` still stacks on top of `poll_id` if someone sets both in Python (default 0, not surfaced — fine); (b) by-elections and SRF measure partially the same reality, so bye+poll at high weights is correlated evidence counted twice *epistemically* — a judgement, not an arithmetic error, and the derived-centres readout exposes it.

### Interactive JS engine (scope 3)

**Ward noise: equivalent despite the different form.** Python multiplies ward×party *tallies* by `exp(N(0,0.10))` (no mean correction); JS multiplies ward×party *shares* by `exp(N(0,0.10)−0.005)`. Both apply i.i.d. lognormal at (ward, party) level before argmax; a per-ward positive constant (the tally scale) and a common per-cell mean factor (`e^{−0.005}`) are both argmax-invariant. The −0.005 correction is a no-op, and its absence in Python is equally a no-op. σ matches (0.10, though JS hardcodes it while Python has `ward_noise_sd`). Level floor `logit(x,1e-6)` matches the adopted `level_floor=1e-6`; dev-deviation floor 0.002 matches SHARE_FLOOR. `wardWinCounts` accumulation and tooltip normalisation (÷nDraws) correct.

**Headless parity run of the actual dev-page engine (3,000 draws, defaults) vs Python REF (5,000):** DA 79/79, ANC **73/75**, EFF 27/27, ASA 25/25, MK 19/19, PA 13/13; P(ANC+DA) **86.6% vs 88.5%**; majority-without-bloc 99.6% vs 99.3%; threshold 136/136; P(excessive) **91.8% vs 95.2%**. All within the disclosed ward-resolution approximation; the page shows the Python reference line, so the gap is visible to readers.

**[LOW] JS combined vote uses the drawn targets, Python uses converged IPF output** — `votesInt=(target+wardT)×totalV` vs Python's `weight@pred`; difference bounded by IPF tolerance (1e-5/1e-6). Negligible.

### Derived stats on the dev page (scope 4)

**[HIGH — display, not math] src/interactive_template.html:922-929 — the near-miss footnote is dead code** — the `near` list (0.05<p<0.5, exactly the footnote the commit e47739a promised) is computed, written to `#coalitionNote`, then **unconditionally overwritten on the very next statement** by the generic "Every pair and triple was checked…" sentence. Readers never see near-misses. The old live page has only the generic sentence, so this is a regression introduced with the redesign. Fix: delete one of the two assignments (presumably keep the near-miss text, appending the generic sentence).

**[HIGH — display] src/interactive_template.html:360 + 397 — duplicate `id="scenarioJson"`** — two textareas carry the same id; `getElementById` fills only the first (the researcher `<details>`). The whole "Reproduce this exactly / Scenario file" section at the bottom renders a **permanently empty textarea**. Leftover from the remove-then-reinstate commits (9d06d0c/818306e). Fix: delete the duplicate section.

**[MEDIUM] Walk-out mid-band silently dropped** — `survives()` lists a member only if `surv≥0.5` or a rescue exists, and the rescue search runs only when `surv<0.10`. A member with surv in [0.10, 0.50) appears **nowhere** — not "survives", no rescue searched even if one exists (contradicting the caption "with the replacement named where one exists"), and no "broken" marker. Likewise fatal exits with no rescue are omitted rather than named (under the SRF/Ipsos presets, DA and ANC exits from every DA+ANC row are fatal-no-rescue and simply absent from the column). Omission-means-broken is a defensible convention, but the 0.10–0.50 band breaks the caption's promise. Fix: search rescues for all `surv<0.5`, and render fatal exits explicitly (e.g. "DA exit breaks it").

**winP / fixed threshold: correct.** `thr[d]` is always 136 and council always 270 in the deduct-only JS engine; seat vectors sum to 270 in all branches, so the subset-sum table against a constant 136 has no stale per-draw assumption. Same for Python (`seat_draws.csv` thresholds all 136, coalitions.analyse consumes them per-draw).

**cushion=med−136: currently exact.** Because the threshold is constant, median(subset sum)−136 equals the median per-draw margin identically — no difference. It becomes wrong only if a non-constant threshold rule (expand) ever returns; a one-line switch to `median(sum−thr)` would future-proof it.

**stability = cushion/med and per-party cushion/med_p: arithmetic correct at the median, with a documented-here caveat.** "x defectors survivable ⟺ x ≤ cushion" is right; share-of-partner = min(cushion,med_p)/med_p is the right heuristic. But it mixes marginal medians (ratio of medians ≠ median of ratio), so the capped-100% cell can in principle disagree with the jointly-simulated `surv` for the same partner. I hunted for live contradictions across defaults + 4 presets: none fired — the caveat is currently theoretical. Also the wording "of **all** councillors" means the coalition's councillors, and the intro paragraph calls the column "Dissent" while the header says "Stability" (cosmetic).

**[LOW] Tile mislabel** — "Chance **the ANC** triggers the excessive-seats clause" displays `overhangDraws/nDraws` = P(*any* party excessive). Measured: any 91.8%, ANC 91.3%, IFP 3.05% — overstatement ≈0.5pt. Use `overhangBy[idx.ANC]/nDraws` (which is computed and then unused).

**[LOW] Kingmaker caption misstates the statistic** — "of all the winning deals your simulations allow, the share that collapse if this party walks out… (the Banzhaf index)". The bar is the *normalised* Banzhaf `sw[p]/Σ_q sw[q]`, whose denominator is total swings across parties, not the count of winning coalitions. "One winning deal in ten needs it" would be `sw[p]/#winning-subsets` — a different number. Reword or change the statistic.

**[LOW] "Others" and "New entrant" participate in coalition enumeration** — both pass the mean≥0.4 filter into `top`, so discovered rows like "DA + ANC + Others" present a synthetic residual lump as a signable partner; Python's enumeration uses real micro-parties. Acknowledged in export_interactive's docstring but not on the page's coalition table.

**Passenger filter: correct as specified**, with one edge: a superset can be suppressed by a subset that itself never displays (subset p<0.03 or p<0.5) — both are below the display cut anyway; and single-party majorities are unrepresentable in the table (no k=1 rows) while the filter would suppress all their pairs. Measured: no party reaches ≥136 in >5% of draws even under SRF@0.6 (DA is clamp-capped at ~0.40 share), so this is theoretical today.

### User ward map vs published map (scope 5)

Tier thresholds identical (≥0.90 solid / 0.75–0.90 fine stripes / 0.60–0.75 bold / <0.60 grey), caption counts match the code, tooltip share cut (≥5%) and "other" bucket (≥0.5%) match render_map.py. Divergences are cosmetic only: JS hatches one challenger at width 3.0/1.6 (Python: up to two challengers, widths 3.2/1.6 with proportional second stripe), and JS tooltips omit the "safe/leaning/toss-up" verdict word. Missing-ward fallback (grey, no tip counts) fine.

### render_map.py inset & render_sheet.py strip (scope 6)

**Inset bands: sound.** The 336-slab area profile + cumulative interp puts each boundary at the party's cumulative seat share of total silhouette area — the area-proportional claim holds to slab resolution. Two latent edges: interiors (holes) are ignored in the slab polygons (city outline has none that matter), and if rounded medians ever summed **over** 270 there's no negative-OTHER guard — `np.interp` clamps and the last parties get silently squeezed. Currently sum=264 → OTHER 6, fine.

**[MEDIUM] render_sheet.py:120-133 — the two-ballots strip neither sums as titled nor matches its own caption.** In the checked-in forecast-sheet.html the bars sum to **134 (ward), 130 (list), 264 (council)** under the headline "135 wards + 135 list seats = 270": rounded `ward_wins_mean` per party don't sum to 135, `max(median−wins,0)` per party don't sum to 135, marginal medians don't sum to 270, and the sub-0.4-mean parties excluded from `summary["parties"]` drop their wards entirely. Since segment widths are `n/total%`, the bars carry invisible ~1–4% gaps. Worse, the **hard-coded figcaption says "Note the ANC's list bar: zero"** while the generated data gives ANC list = 1 (75−74) — the prose contradicts the graphic it captions. Fix: allocate the ward bar by rounding-with-remainder to exactly 135 (with an explicit "Smaller parties" ward bucket = 135−Σnamed), derive list = 135-constrained residual, and compute the caption's ANC claim from the data or soften it.

### Registers & docs (scope 7 + contradictions vs the logs)

- **polls.json vs POLLING.md: numbers agree** for SRF Q1/Q2, DA internal. **[LOW]** The ipsos-w2-2025-metros entry carries PA 0.04 and IFP 0.02 that appear nowhere in POLLING.md's table — undocumented additions (plausible from the full Ipsos release, but the register's provenance table should carry them).
- Poll/bye clamp arithmetic identical in both engines (verified above). `POLLING_SPAN=4` and the `_leanSign` parameter in the JS are dead code (Python default `polling_span` is 8 — would be a divergence if the JS lean path existed; it doesn't).
- **[MEDIUM] montecarlo.py:657, summary "p_overhang" is structurally 0.0 under deduct** — `(council_sizes>270).mean()` can never fire when the council is fixed, so the console prints the self-contradicting "P(any overhang): 0.0% by party: ANC 95.2%", and `forecast_summary.json`/REF carry `p_overhang: 0.0` while `p_excessive_by_party.ANC = 0.952`. Nothing downstream displays the dead metric (sheet and dev page correctly use the excessive rates), but it's a trap for the next consumer. Rename/redefine as P(any party excessive).
- **[MEDIUM] METHODOLOGY.md §5A step 6 and §5B still teach the expand rule** ("council expands… median ~281, threshold ~141", DA 81, ANC+DA 86.5% at per-draw thresholds, item J "council-expansion reading unverified… task #20") — all contradicted by MODEL-LOG 1.17/1.18 (deduct is law, Laingsburg verified, threshold 136 fixed, task #20 closed) and by the regenerated outputs (ANC+DA 88.5%, DA 79). MODEL-LOG 1.17(2) itself orders this corrected site-wide; METHODOLOGY.md predates the resolution and was never revisited. The **dev page's own colophon** (template line ~404: "overhang treatment per plan §3.7, statutory fine print unverified against an IEC worked example") likewise contradicts the tile two screens above it ("the excessive-seats law keeps the council at 270"). MODEL-LOG 1.18's "P(ANC+DA) 86.5%" also doesn't match the actual adopted run's 88.5% (86.5 was the pre-adoption expand figure).

## JS vs Python parity summary

| Quantity | Python (5k, REF) | JS dev engine (3k, measured) | Δ |
|---|---|---|---|
| DA / ANC / EFF / ASA / MK / PA medians | 79 / 75 / 27 / 25 / 19 / 13 | 79 / 73 / 27 / 25 / 19 / 13 | ANC −2 |
| P(ANC+DA) | 88.5% | 86.6% | −1.9pt |
| P(majority w/o ANC bloc) | 99.3% | 99.6% | +0.3pt |
| P(excessive clause) | 95.2% (ANC) | 91.8% (any; ANC 91.3%) | −3.4pt |
| Threshold | 136 | 136 | — |
| Deduct allocator on identical inputs | — | — | **0/3000 mismatches** |

Divergence sources, all disclosed or second-order: ward-resolution vs 865-VD model (drives the ANC −2 and excessive-rate gap); ward-level vs VD-level turnout noise; `vl` built from `turnout_2026_level` (cap-after-scale, 2024 registration weights) vs Python's cap-before-scale on 2026 weights; JS medians are order statistics (upper median) vs numpy interpolation (≤0.5 seat); JS lacks Python's [0.02,0.95] turnout-rate clip (unreachable at σ=0.08); OTHER lump carries a judgement γ=0.9.

## Verdict

**The mathematics is fit; the page furniture is not yet.** Both engines implement the amended Schedule 1 deduct rule exactly (modulo the equality-trigger reading, ~0.25% of draws, no headline effect), the bloc-leak/evidence/poll arithmetic is internally consistent and mirrored, and JS↔Python parity is within the disclosed approximation everywhere I could measure. I would promote the dev interactive to the live site **only after** three fixes, none of which touch the engine:

1. **Remove the duplicate `scenarioJson` section** (empty "Reproduce this exactly" textarea at the bottom of the page) and **resolve the double `coalitionNote` assignment** so the near-miss footnote actually renders — both are visible defects on first scroll.
2. **Update the colophon (and METHODOLOGY.md §5A/§5B) to the deduct statute** — the page currently cites the superseded "§3.7 expansion, fine print unverified" language while its own headline tile asserts the opposite; publishing both is a credibility hit MODEL-LOG 1.17 already ordered fixed.
3. **Close the walk-out display gap** (rescue search for all surv<0.5; name fatal exits) and correct the sheet's two-ballots strip sums/caption ("ANC list bar: zero" vs the actual 1) — these are the places a careful reader can catch the page contradicting itself.

The equality-trigger question (`>` vs `>=` in both deduct loops) should be logged and either fixed or explicitly ruled — it is the one place the code and the statute's wording measurably part ways.