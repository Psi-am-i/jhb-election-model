# Pre-registration — the entrant COUNT as the group budget's missing covariate

⛔ **OUTCOME, 2026-09-07: P2 IS FALSIFIED AND THE CHANGE WAS NOT MADE.** The
panel below scores an estimator of one population against realisations of a
DIFFERENT one. On the population the budget is actually spent over, the shipped
budget beats the count route. **Nothing below is edited** — a pre-registration
that is corrected after the answer is not one. The result is MODEL-LOG §1.200.

**Written 2026-09-07, BEFORE a line of the change.** Arises from the pollster
review of §1.198/§1.199 (F6b) and from the count decomposition in §1.199 §3.

⛔ **The companion recommendation — F6a, "fix the comparator window, it captures
37% of the reach gradient" — is NOT taken, and P0 records why.** It was measured
on a record the re-emit replaces.

---

## P0 — What is NOT changing, and the measurement that says so

The pollster's F6a was derived on the **pre-2021** record (77 rows), where it
reported the estimator capturing `0.479` of a record gradient of `1.302`. On the
**widened pre-2026 record — the one every emitted spec will carry** — I get:

| record | record's own gradient (top vs bottom reach quartile, log) | estimator's gradient | captured |
|---|---|---|---|
| pre-2021, 131 rows | **−0.001** (0.2105% vs 0.2102%) | +0.205 | the record has no gradient to capture |
| pre-2026, 304 rows | **+0.722** (0.2466% vs 0.1198%) | +0.716 | **99%** |

So on the shipping record the comparator window tracks the reach gradient almost
exactly, and on the pre-2021 record the *record* shows no gradient while the
estimator manufactures one. **F6a is an artefact of the population it was
measured on.** `comparators()` is left alone.

*Falsified if the widened record's gradient and the estimator's differ by more
than 0.10 in log units, under the quartile-mean definition stated above.*

## P1 — The change

`_arrival_total_prior` returns a scalar per target: the pooled mean of past
city-years' entrant totals. It predicts a TOTAL for a roster whose SIZE it never
sees. The count decomposition (§1.199 §3) is exact —

    count ratio 2.2468 x size ratio 0.7874 = 1.7690 = observed total ratio

— so the quantity that moved between 2016 and 2021 is the number of parties
standing, and that number is **published on the nomination roster before polling
day**. §L6 calls this a *"missing covariate (how fragmenting a cycle is)"*. It is
the entrant count.

**The budget becomes `n_entrants x per-entrant mean`**, where `n_entrants` is the
count of undeclared entrants the emit is about to seed and the per-entrant mean
is the unconditional mean of the prior entrant record.

## P2 — The scored comparison, walk-forward, 16 city-years

Measured 2026-09-07, each target predicted only from cycles strictly before it:

| route | Σ\|err\| | mean\|log err\| | mean log err | within 2x |
|---|---|---|---|---|
| budget (shipped) | 30.2537% | 0.815 | **−0.513** | 44% |
| **count** | **25.0877%** | **0.547** | **+0.114** | **75%** |
| geometric midpoint | 23.1752% | 0.569 | −0.199 | 69% |
| log-blend w=0.75 | 22.9580% | 0.542 | −0.043 | 69% |

*Falsified if any figure in the first two rows moves by more than 1e-4 when
re-derived on the same tree.*

⛔ **THE BLENDS ARE NOT TAKEN even though two of them score better on Σ|err|.**
Their weight is chosen on the same 16 cells they are scored against; the count
route has **no free parameter** — the count is observed and the per-entrant mean
is the record's. This is the §L6 recency decision again and it is decided the
same way: parsimony, not score.

## P3 — What this does to the group rescale, stated in advance

`arrival_rules` rescales by `k = want / have`, `have = Σ base_i` over undeclared
entrants. Under P1, `want = n x per-entrant mean` and `have ≈ n x mean(base_i)`,
so **`k` moves toward 1 and the rescale approaches the identity.** The change is
therefore not a re-tuning of the budget; it is the finding that **the per-party
centres, summed, are already the better estimator of the group total** — 25.09%
against 30.25% — and that the flat historical total was the thing doing damage.

*Predicted: `k` at Johannesburg 2021 moves from ≈0.21 to within [0.7, 1.4].
Falsified outside that.*

## P4 — The instrument gains resolution, and that is the point

The budget route makes **one** prediction per target, so §L6's out-of-sample
table has two effective observations (§1.198). The count route makes a
**different prediction per city**, so the same panel becomes a **16-cell**
instrument. That is a change in what can be measured at all, and it is the
strongest argument for the covariate independent of its score.

*Falsified if the per-city predictions are found to be a deterministic function
of the target, i.e. if the count does not vary across cities within a year. It
does: 2021 runs 10 to 34.*

## P5 — What decides it

* **The 16-cell walk-forward above is the primary evidence** and it is already
  taken. It is scored against realised group totals — a property of the world,
  not a ratio against our own output (CLAUDE.md rule 10).
* **`compare_history` is NOT the arbiter here.** The seeded-arrival channel is
  inert in the live 2026 forecast (`seeds` empty, `arrival_group: null`) and
  reaches only the 2021 column of the panel. A panel score may not be recruited
  afterwards as though it had been the test.
* **KEY 4 cannot fire** — nothing here touches `sd_for` or `theta_prior`.
* Predicted seat effect on the live forecast: **zero**, because the channel is
  not reachable at 2026 without a roster. That is the pass condition, not a
  disappointment.

## P6 — Known asymmetries, declared

* **The per-entrant mean is itself a mean over a right-skewed record**, and the
  count route inherits that. It over-predicts where a city fields many tiny
  parties (CPT 2021: 28 entrants, count route 6.34%, realised 6.18% — close;
  JHB 2021: 34 entrants, 7.70% against 2.37% — not) and under-predicts where a
  city fields few large ones (MAN 2016: 5 entrants, 1.05% against 4.84%).
  **The count fixes the level and not the dispersion**, and the residual is
  still wide.
* **The count is known only after 16 September.** Before nomination lists close
  the model must fall back to the shipped budget, so both estimators stay in the
  code and the fallback must announce itself.
* **This changes what `_arrival_total_prior` IS**, so §L6, §L7 and the
  docstring's four target values all move in the same commit.
