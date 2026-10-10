# Pre-registration: did by-election evidence predict the next real result beyond the model? (item 19)

Written 2026-10-10, before `src/bye_value.py` exists and before anything it
computes has been run on real data. Not to be edited after the run.

Source: SPEC Revision 2, R2.4 (the test) and R2.5's P19 block
(`audits/2026-10-09-model-fixes/spec/SPEC.md`); BRIEF.md decision 19 (owner,
2026-10-09: "by elections we need to use history as the judge of whether they
predicted anything not already predicted by model").

**The cross-ballot caveat, stated wherever this test's result is quoted.** The
archive's by-elections start in 2022-02, so the only real result after them is
the 2024 provincial ballot. By-elections are local ward contests; the outcome
is a national-provincial list ballot. This is the whole record.

## P19, copied from R2.5

**P19 (the test, then arm E against D).**
- Test prediction, written before it is computed: the under-1% class has
  fewer than 40 pairs with any contest beyond one, the cross-ballot noise
  dominates, and its weight comes out 0. The 1%-and-over class: no prediction
  of sign; its 5th-percentile gain is within ±0.3 points of 0.
- If both weights are 0, at Johannesburg 2026: the All Citizens Party's centre
  returns to about its arrival seed (item 9 measured 0.050% list mean at
  `w_bye = 0`), mean seats from about 2 to under 0.2; Truth and Solidarity
  0.111% → about 0.06%; the PA loses the 0.78-point by-election tilt (item 7's
  step table) on top of arm D; the DA's +0.093 and MK's +0.106 weighted deltas
  no longer reach the centres. Item 7 measured `w_bye = 0` on the published
  model at PA 22.30 and DA 64.75 seats; the direction (PA down, DA down, ANC
  up) is predicted again here, the size is not, because arm D's centres differ.
- No backtest number moves: no backtest target reads the by-election file.

The first bullet is scored when `bye_value.py` first runs on real data. The
second and third are arm E's and are scored at the batch's measurement (SPEC
§7 step 11, R2.6).

## Dated note, 2026-10-10: what slice M3 changed under P19

P19 was written against the tree before items 11, 16 and 17. The baseline `B`
uses `mu_θ` from `levels._shrunk`, and all three now act on it:

- **Item 11a:** the size centre is evaluated at the party's current national
  size, not at the mean size of its own observations.
- **Item 16:** a party's own observations count only within the size window
  `h` (`levels.size_window`, JUDGEMENT-CALLS §A52). The window `B` uses is the
  one `size_window` derives at a 2024 target. Measured before this note
  (2026-10-10, in-process, read-only): `h = inf` at a 2024 target (status
  "derived", best 2.0, 265 observations scored; the same walk as at 2021,
  because the walk visits local-election targets only). So item 16 filters
  nothing in `B` on the current archive.
- **Item 17:** a party with a national share and no θ record of its own takes
  the size centre at that share, where it previously took the flat common
  mean.

None of P19's predictions names a quantity these move: the under-1% class's
weight and the ≥1% class's gain interval are stated without reference to
`B`'s level. The predictions stand unchanged. What the three items change is
which residual `e = actual − B` each pair carries, so the measured `w` and `G`
are those of the M3 tree, not of the tree P19 was drafted on.

## Method decisions R2.4 leaves open, fixed here before the run

1. **Population.** Every (party, metro) pair where the party stood in at least
   one by-election in the metro (ward prefix from `cities/<slug>.toml`) in
   `data/raw/byelections/byelections_SA_vd_party.csv`, dated strictly after
   the 2021 LGE polling day (2021-11-01, `byelections.load_byelections`' lower
   bound, the delimitation the deltas are taken in) and strictly before
   2024-05-29; and with a positive list share at the 2021 LGE or on the 2024
   provincial ballot in that metro. Party names through `parties.canonical`.
   No party is named or excluded by name; a label with no list vote (an
   independent candidate) falls out by the list-vote condition.
2. **The delta.** `byelections.py`'s weighted delta for the party in the
   metro: the contests above, each against the same ward's 2021 ward-ballot
   result, weighted `exp(−age/τ)·√votes·ρ` with the age taken to 2024-05-29,
   `τ` the module's default (18 months) and `ρ` the similarity to the metro's
   2021 ward-ballot profile. A contest whose ward has no 2021 base is skipped,
   as `byelections.py` skips it. The function is lifted out of
   `byelections.main` so both use one definition.
3. **The PR conversion.** As `blended_centres`: divided by the party's 2021
   ward/PR ratio in that metro where its 2021 PR share exceeds 0.001 (clipped
   to `WARD_PR_RATIO_MIN/MAX`), additive otherwise. One definition, imported.
   The model's `BYE_MIN_WEIGHT` admission gate is not applied in the test
   (R2.4 does not apply it); every pair's weight sum is reported.
4. **`B`.** `B = s_2021 / exp(mu_θ)`. `s_2021` is the party's PR share in the
   metro's 2021 LGE (`levels._citywide`); with none, `B = 0`. `mu_θ` is
   `levels._shrunk(theta_record(2024 target), current=…, h=…)`: `current` is
   each party's share of the metro's 2019 national ballot (the national
   election before 2024, as the model's baseline is the national election
   before its target), one call per metro on the one pooled record, `h` from
   `size_window` at the 2024 target. A party with a 2021 list share and no
   `mu_θ` (no 2019 share and no θ record) takes the common mean that
   `_shrunk` returns, as `levels.spine` does (`mu_t.get(party, c_t)`); the
   count of such pairs is reported. Mergers are not applied to `s_2021` (the
   model applies them at a live target's roster; there is none at 2024).
5. **The outcome.** `actual_2024` is the party's share of the metro's 2024
   provincial ballot (`levels._citywide` on `npe2024_<CODE>`), 0 if absent.
6. **Classes.** By `s_2021` in that metro: under 1% (including 0) or at 1%
   and over. The edge is one named constant used by `bye_value.py` and
   `blended_centres`.
7. **Leave one metro out.** For each metro and class, `w_(−m)` is
   `max(0, Σeδ / Σδ²)` over the class's pairs in the other metros (0 where
   `Σδ² = 0`). `G = mean|e| − mean|e − w_(−m)·δ|`, pooled over every pair of
   the class, each with its own metro's `w_(−m)`, in points of share.
8. **Bootstrap.** 2,000 resamples of the metros that hold any pair, drawn with
   replacement, numpy `default_rng` with a fixed seed recorded in the
   artefact. In a resample, the hold-out is by metro identity: every copy of a
   drawn metro is held out together and fitted on the copies of the others. A
   class with no pair, or no fit set, in a resample scores `G = 0` there. The
   5th percentile is numpy's default (linear) percentile.
9. **Rule.** A class with fewer than 10 pairs takes weight 0 ("not
   measurable"). Otherwise its weight is the slope fitted on all its pairs
   (floored at 0) if the 5th percentile of its `G` is above 0, else 0.
10. **Secondary, reported and not deciding.** Each contest's delta predicted
    from the same party's other contests in the same municipality (their
    weighted mean), against predicting 0. R2.4 names "all 311 contests
    nationally"; the 2021 ward bases on disk cover the eight metros only, so
    the secondary covers the metro contests in the window, and says so.

## Scored, 2026-10-10 (appended after the run; nothing above is edited)

Scored against a `src/bye_value.py --out` build of commit 03bf2f0's test on
the tree at 6c570be, into a scratch directory, `PYTHONHASHSEED=0` (writer,
measured). The coordinator's re-derivation and the blind reviewer's
independent plain-loop implementation reproduced the same class figures
(`reviews/M4-SUMMARY.md`). Cross-ballot: ward by-elections from 2022-02
against the 2024 provincial list ballot.

| P19, first bullet | measured | scored |
|---|---|---|
| the under-1% class has fewer than 40 pairs with any contest beyond one | 34 pairs, 11 with two or more contests | **held** |
| the cross-ballot noise dominates | G −0.017 points, 5th percentile −0.043 points: no out-of-sample gain to separate from noise | **held** (qualitative; no threshold was stated) |
| its weight comes out 0 | weight 0, "no measurable gain" | **held** |
| the 1%-and-over class: no prediction of sign | G −0.070 points | not scored (no prediction) |
| its 5th-percentile gain is within ±0.3 points of 0 | 5th percentile −0.318 points | **falsified**, by 0.018 points |

The second and third bullets are arm E's and stay open until the batch's
measurement (SPEC §7 step 11).

**Method decision 1 was wrong about independents.** It says "a label with no
list vote (an independent candidate) falls out by the list-vote condition".
It does not: the 2024 provincial ballot carried independent candidates, so the
canonical `IND` label has a positive 2024 share in eThekwini, Johannesburg and
Mangaung and enters the under-1% class as three pairs (writer, measured from
the scratch build's `pairs`). `IND` is a label covering several candidates, not
a party in the sense the model forecasts. Removing the three pairs (measured,
`bye_value.evaluate` on the remaining pairs, same seed): under-1% class 31
pairs, 9 with two or more contests, G −0.017 points, 5th percentile −0.0435 →
−0.0351 points, weight 0; the ≥1% class is unchanged (it holds no `IND`
pair). The verdict does not move. The population stays as pre-registered;
changing it after the result would be a second, unregistered test.
