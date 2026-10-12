# Total review: coordinator's synthesis (2026-10-09)

The reviewer's full report was returned as text; the harness refused its file
write. It is summarised here, with the coordinator's re-derivations.

## Re-derived by the coordinator (served draws, base cell, 5,000 draws, draws_sha256 3b25be8f)

| quantity | reviewer | coordinator |
|---|---|---|
| DA more seats than ANC / ANC more / tie | 50.4 / 48.1 / 1.5% | 50.4 / 48.1 / 1.5% |
| median seats, ANC and DA | 66 / 66 | 66 / 66 |
| PA list − ward gap, mean (min, max), points | −5.53 (−15.22, −1.20) | same |
| PA draws with a gap below −1.76 / below −6.76 | 99.9 / 15.5% | same |

Not re-derived: the four-weakest-calls re-seat (ANC 66, DA 66), P(ANC ≥ 70
wards) = 41.6%, and the 79 draws close to rule A.

## Findings for the owner

1. **Our prediction and our forecast name different largest parties.** Rule A
   gives ANC 70, DA 65. The forecast gives the DA more seats in 50.4% of
   simulations and the ANC in 48.1%. Under item 16 each ANC ward call is one
   seat, so four marginal calls decide it. The backtest never reached an
   overhang regime: no past city-year had one.
   - **Coordinator's argument for keeping rule A:** in the 24-election backtest,
     calling every ward for its favourite did not overcount the leader's wards
     against what actually happened (MODEL-LOG §1.290, P1: 6 of 24). So the
     gap between modal calls and the model's mean ward wins was not a gap with
     reality.
   - **The reviewer's alternative:** when item 16 fires, call that party's wards
     down to its median ward-win count. That gives ANC 66, DA 66, a tie.
   - **What would settle it:** a past council with overhang, which the metro
     panel lacks.
2. **PA's ward/list split has no precedent.** In the model's draws PA's list
   vote averages 5.5 points below its ward vote, a model property that the
   restructure now publishes. One explanation is that ward-ballot-only
   by-election evidence inflates PA's ward share; the other is a real expected
   split. Comparing PA's ward and list shares in the by-election and 2024 data
   behind its prior would separate them. This is a model-tier question and
   should be settled before our prediction is sealed.
3. **Slice C is outstanding:** the single simulation is still on `/forecast`;
   there is no seal, ledger or ranking identity; G11 and G16–G19 are not built;
   the card header does not name its ballot.

## Record defects to fix (after the B2 design returns; it reads these files)

- **Diff-review dispositions.** Write the accepted and declined list for the
  slice A and slice B reviews into `s2/`.
- **Owner attributions.**
  - The owner did answer "old sealed links - fine" (2026-10-08) and "1. agree
    2. agree" to S0 decisions 1 and 2. Record both in `S0-SYNTHESIS.md`.
  - JUDGEMENT-CALLS §Q4's "no OTHER party" is the coordinator's S1 resolution.
    Relabel it.
  - S1 item 9 is still open. 94bbd6e committed the claims build; it did not
    release it.
- **Typed figures.**
  - §R1's 719 / 12 / 29.6% move into a MODEL-LOG entry that points at the probe.
  - §Q1 stops copying "the ANC, excess 11".
  - `prereg/README.md` gets a dated note that §1.291 corrected 739 to 737.
- **Reader text.** "your prediction is scored on the list vote" becomes "the
  vote is scored on the list ballot; seats and ward calls come first".
- **Known gap.** `declares.py` cannot see anything served or held in D1. Record
  it in QC.md §6.
- **S5.** The whole suite must run with `PYODIDE_NODE` set.
- **Slice C must also define** what happens with no seal of ours at the lock, a
  rollback after the last seal, and a D1 clear after our seal.
