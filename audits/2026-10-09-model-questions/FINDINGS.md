# Model questions, 2026-10-09: findings

The investigator's write was refused; the coordinator saved this, condensed
from the report. Raw outputs and scripts are in `data/`; the pre-registration
is `PREREG-ward-list-fix.md`, scored here.

**Coordinator re-derivations (verified):**
- The Coloured pool's expected vote is 69,761, or 7.11% of the city, from
  `pools_2026.json`.
- The PA's centre is 7.57%, from `site/draws` manifest centres (stage
  30_centres).

## Ranked findings

1. **The Coloured pool's mean is outside every real split (a defect, and it moves
   the forecast).**
   - The PA's centre (7.57%) exceeds the whole Coloured pool (7.11%). The
     balance step gives the PA about 85% of the Coloured vote (record max
     43.7%) and pushes the DA to about 6% (record min 24.5%).
   - JUDGEMENT-CALLS (around line 605) already records the PA asking for about
     102% of the Coloured vote.
   - No split rule can fix this: it sits in the mean. Whether the PA's level is
     right is a centres question.
2. **The PA's ward/list gap was introduced at `2ac4c1e`** (2026-09-23, §1.252).
   - Contestation is measured by ward count. Going from the PA's 2021 slate
     (38.5% of wards, holding 95.5% of its list vote) to all wards multiplies
     its ward ratio by about 2.6, clipped to 2.0.
   - Neutralising that alone gives a gap of +0.07 (from −5.52), PA seats
     23.95 → 16.51, and ward wins 10.4 → 4.8.
   - **The PA is the only party outside the real range** (−1.76 to +6.16 over
     40 files).
3. **The within-pool split's tails go past history** (by design: one pool
   concentration, A, means member i gets α_i = m_i·A). The ANC and the EFF set A;
   small members were historically far steadier.
4. **The canary: 46 parties have no level shock.**
   - All 46 are seeded arrivals. `montecarlo.py:2882-2883` zeroes their shock on
     the claim that "the band carries the uncertainty". The band is read by
     nothing: every seeded party is pooled and `continue`s before its band is
     looked up (`:2772`).
   - Found in MODEL-LOG §1.198, called "the owner's decision", and never
     registered in JUDGEMENT-CALLS: a defect.
   - **Effect is small:** seeded parties are already wider than non-seeded ones
     at equal centre, because the split dominates.
5. **The centres sum to 117.05%, and every drawn mean equals centre ÷ 1.17.** The
   centres bind in proportion, not in level: a definitional difference, not a
   contradiction.
6. **After the PA fix, the DA's gap falls below the real minimum in 17.3% of
   draws.** The 2021 ratio is applied multiplicatively at other share levels.
   Flagged.

## The split's "history" is not observed

The yearly splits that fit A are the 2026 Johannesburg composition vector
multiplied by each metro-year's citywide shares (`pools.py` ~6355). So:
- a party's within-group "move" is its citywide move seen through a fixed
  composition;
- Cape Town and eThekwini are computed with Johannesburg's composition;
- parties absent from the 2026 spec are missing;
- the PA's 43.7% of Johannesburg's 2021 Coloured vote is implied, not measured.

## Records against the draws (owner's Amendment 2)

**Group ceilings**, the largest ordinary move in points:

| group | ceiling | held by |
|---|---|---|
| Black African | 19.8 | ANC, Tshwane 2011→16 |
| Coloured | 39.8 | PA, Johannesburg 2016→21 |
| Indian/Asian | 31.3 | DA, Johannesburg 2016→21 |
| White | 22.8 | DA, Johannesburg 2016→21 |

**2026 draws past the ceiling:**

| group | any reason | from the split alone |
|---|---|---|
| Black African | 53.6% | 18.0% |
| Coloured | 63.4% | 0.0% |
| Indian/Asian | 2.5% | 0.2% |
| White | 5.6% | 2.2% |

The rest is the forecast's level shift.

**What the owner's direction does not capture:**
- Moves scale with size: median |move|/start is about 0.5 below 1% share and
  0.05–0.22 above 20%, so a flat ceiling binds large parties only.
- Moves come in mirror pairs: the ANC's loss is about the EFF+ASA gain, and the
  DA's −33 is the PA's +40 in the Coloured group.
- One election holds three of the four ceilings (Johannesburg 2016→21).
- Per-metro ceilings differ by 2–3×.
- The ANC's Black African moves are a trend (−18 twice), not scatter.
- MK has a national record but no within-group record.

## The PA fix: vote-weighted coverage, pre-registered and tested

**Change:** in `now/was` (`montecarlo.py` ~4802), measure contestation as the
share of the party's previous list vote in wards it contests, not as a count of
wards.

**World test, with no model** (316 consecutive party pairs, MAE in predicting
the actual ward share):

| form | all | slate changed > 0.2 | slate at least doubled |
|---|---|---|---|
| count | 0.427 | 0.564 | 0.689 |
| none | 0.291 | 0.218 | 0.240 |
| vote-weighted | 0.265 | 0.170 | 0.281 |

**Pre-registration F1–F6, all held:**
- the PA's gap is −0.19, with no draw below −1.76;
- PA seats 23.95 → 16.85;
- list votes are identical.

**Panel (24 city-years):**
- B1 held: list MAE is identical.
- B2 is partly falsified. Ward MAE improves overall (2.990 → 2.901), but four
  city-years worsen by more than the 0.15 limit: ETH 2016 +0.43, CPT 2021
  +0.25, ETH 2021 +0.18, JHB 2021 +0.15.
- B3 held: coherent seats 735 → 721.
- C1 held: vote-weighted 2.901 < none 2.940 < count 2.990.

**Not separated:** vote-weighted ties "no contestation change" on coherent
seats (721 = 721). The count form is the worst of the three. The choice between
the other two is the owner's.

**Remaining fragility:** `r0` is clipped to [0.5, 2] before the change is
applied. AIC, Buffalo City 2011→16, is predicted at 7.79% against 2.95% under
both forms.
