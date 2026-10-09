# Item 7, candidate corrections: pre-registration (written before the runs)

Written 2026-10-09, before any candidate below was run. Runs are in-process
`run_model`, joburg 2026, seed 20261104, 1,000 draws each, alone and stacked on
the item-6 vote-weighted contestation patch (`votecov.make('2026')`).
Baseline reference (published run, model-questions q1_base, 5,000 draws): PA
23.95 seats, DA 66.53 seats; item-6 alone: PA 16.85, DA 68.56.

Each candidate is a monkeypatch; the repository is not edited.

| id | change | expected PA seats | expected DA seats | expected PA share of Coloured vote (median) |
|---|---|---|---|---|
| a1 | PA vector: 3.7% of its weight outside the Coloured pool (2024 Duncan-Davis minimum), level unchanged | within 1 of base | within 1 of base | falls a little, still above 0.80 |
| a2 | PA vector: 16% outside (2024 two-group Goodman estimate), level unchanged | within 1.5 of base | within 1.5 of base | about 0.75 |
| b1 | PA's own θ/ρ records dropped: both multipliers at the size centre for its record's base size (θ 1.074, ρ 0.826); by-election tilt and shrink run as now | 10-14 (base); 7-10 (on item 6) | +2 to +5 | 0.40-0.50 |
| b2 | as b1 with the size centre at the PA's current size (θ 0.921, ρ 0.762) | 1-2 below b1 | as b1 or slightly more | slightly below b1 |
| c | `w_bye = 0` (all parties) | -1 to -2 (q1_w_bye0 had 22.30) | -1 to -2 (q1 had 64.75) | falls about 0.05 |
| d1 | PA centre set so its drawn mean list share is 2.93% (its record 0.41 rate × the Coloured pool, plus its 0.6% outside weight) | 9-12 (base); 7-9 (item 6) | +3 to +6 | about 0.41 |
| d2 | PA centre set so its drawn mean is 5.65% (record 0.41 + the pool's largest real one-cycle rise, 0.383) | 20-23 | within 1.5 | about 0.79 |
| a2+b1 | both | below b1 by 0-1 | as b1 | about 0.35 |

Direction claims that would falsify the mechanism account in FINDINGS.md:
- if a1/a2 move PA seats by more than 2, the vector, not the level, is
  carrying the PA's seats;
- if b1 leaves the PA's Coloured rate above 0.60, something other than the
  spine multipliers holds the level up.
