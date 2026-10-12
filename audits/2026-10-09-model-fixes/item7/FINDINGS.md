# Item 7: the PA's centre against the Coloured pool (2026-10-09)

The investigator's write was refused; the coordinator condensed this from the
report. Its pre-registration (`PREREG-candidates.md`) was written before the
candidate runs. Data and scripts are in this directory.

**Coordinator re-derivations (verified):** the PA got 2.960% of the 2021
Johannesburg list vote, and 2.909% of 1,415,548 votes in the 2024 national
election.

## Finding: the PA's level is the defect

The spine multiplies the PA's real ~2.9% by multipliers measured during its
2016–2021 emergence:
- θ = 1.995, from observations off bases of 0.014%–0.29% (3.07, 2.44, 1.10,
  10.9, 100.3, 34.7, 19.7, 1.49);
- ρ = 2.741.

No panel party with a base of 1.5–5%, which is the PA's size now, has a θ above
1.58 (n = 39).

**The centre, step by step:**

| step | value |
|---|---|
| 2024 national share | 2.909% |
| × θ 1.995 | 5.80% |
| 2021 list share | 2.961% |
| × ρ 2.741 | 8.12% |
| blend | 6.43% |
| by-elections | 7.21% (+0.78pp) |
| shrink | 7.57% |
| renormalised | 6.47% |
| drawn | 6.30% |

Of the 4.31 points between 2.90% and the 7.21% centre, the multipliers carry
3.53 and the by-elections 0.78.

`_shrunk` evaluates the size centre at the mean base of the party's own
observations (about 0.1% for the PA), not at its current size. That applies to
every party; whether it is a defect is a judgement.

## The pool size is right; the vector is right for 2021 and behind 2024
- **Pool size.** Registration, turnout and expected vote (69,761, 7.11%) match
  2021 and the turnout of near-homogeneous Coloured wards.
- **Vector.** The 2021 fit is 99.4% Coloured, on the Duncan-Davis corner. The
  2024 proven minimum for the share of PA voters who are not Coloured is 3.7%.
  Changing the vector moves PA seats by at most 0.27.
- **The two layers disagree.**
  - The pool layer puts 99.9% of the PA's vote among Coloured voters.
  - The ward layer puts 43% of it in wards under 10% Coloured, which would need
    about 180% of the Coloured voters there (argued).
- **Real results.** The PA's share of the Coloured vote is bounded at
  13.8–41.0% in 2021 and 6.8–42.9% in 2024. The largest proven share in any
  other metro in 2024 is 16.2%. The 2026 draws give a median of 88.3%.

## A guard that sees it (specified, not built)
- **Quantity:** each party's realised share of each pool's vote per draw.
- **Threshold:** the party's own record (its largest Duncan-Davis upper bound
  in this city's real results) plus the largest one-cycle rise any party has
  made in that pool, in any metro.
- **Test:** it fires when a pair exceeds the threshold in more than 5% of
  draws.
- **Constructed violation (×12 centre):** the PA fires in all three pools,
  while every existing counter reads 0.
- **Reverted** (centre at its record): quiet.
- **Live:** PA/Coloured fires in 69% of draws.
- **Against real 2021 results:** it flags 12 of 1,252 outcomes (ASA ×5,
  PA ×4, VF+ ×3). It is a tripwire, not a constraint.
- **Floor side:** the DA gets a median 4.0% of the Coloured vote, below its
  2024 proven minimum in 66% of draws.

## Candidate corrections (1,000 draws each; pre-registration 22 of 24 held)

| id | change | PA seats | PA, on the item-6 fix | DA seats |
|---|---|---|---|---|
| base | none | 23.95 | 16.85 | 66.53 |
| a1 / a2 | vector 3.7% / 16% outside the pool | 24.01 / 24.22 | ~17 | ~66–67 |
| b1 | drop the PA's own θ/ρ record | 12.35 | 8.54 | 69.47 |
| b2 | size centre at current size, for all parties | 11.15 | 7.73 | 70.90 |
| c | no by-election tilt, for all parties | 22.30 | 15.68 | 64.75 |
| d1 | cap at the PA's record share of the pool | 11.17 | 7.74 | 70.92 |
| d2 | cap at record + the largest real rise | 20.95 | 14.72 | 67.06 |

The ANC gains about 3.5–4.2 seats under every level candidate.

## Correction (2026-10-09, after the specification review)

Candidate b2 was labelled "size centre at current size, for all parties". The
script (`scripts/variants.py`, lines 15-17 and 46) patches the **PA alone**, and
replaces the PA's own θ/ρ with the size centre, which also drops the PA's own
record. The "PA 11.15 seats" result belongs to that PA-only change.

The general rule the owner chose (item 11: every party's size centre evaluated
at its current size, own records kept) moves the PA's spine level only from
6.43% to 6.05% (`spec/SPEC.md` §0 O1, computed from the spine, no model run).
The coordinator relayed the mislabelled result to the owner as the effect of
the general rule. That was wrong.
