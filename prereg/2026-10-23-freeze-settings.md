# The frozen Johannesburg 2026 forecast: pooled γ, placeholder fix, ActionSA call withdrawn

Written before any code change, re-emit or run, on 2026-10-23. Owner,
answering OWNER-DECISIONS item 33: "go with your reccommendation and remove my
action sa judgement call which just serms to ,make things compolicated. we cna
deal with that later."

**Already known before this was written:**
- MODEL-LOG §1.333, with seed 20261104 and 5,000 draws on 261b29f:
  - B (the site) gives P(ANC largest alone) 58.1% and DA 33.8%.
  - BF (placeholder fix) gives 61.2% / 30.9%.
  - GP (pooled γ) gives 59.1% / 32.9%.
  - The γ arms move no mean list share.
- MODEL-LOG §1.330 (21 October tree) compared the run with ActionSA held at
  17.6% against the run without the call:
  - ActionSA's own centre was 12.64%.
  - ActionSA's seats were 40.5 with the call and 29.3 without.
  - The ANC was largest in 60% of simulations with the call and 46% without;
    the DA in 36% and 49%. These figures split ties.

## The change

Johannesburg 2026 only; Tshwane is not changed.
1. Fold files carry each row's fit status (`fold.fit_status`), and
   `load_parameters` skips any row that is not a real fit, so `gamma_recent`
   and then 1.0 apply as `run_model` intends (DATA-QUALITY 21). This reaches
   every target whose fold has placeholder rows, past targets included.
2. γ for Johannesburg 2026 comes from folds 1 and 2 pooled
   (`fold.py --pool 1,2`): one through-origin fit over both folds' VD rows.
3. `[party.ASA]` is removed from `judgements/joburg-2026.toml`.
4. Re-emitted: the fold files (with the status column) and the pooled file. The
   width record is re-emitted too, because `montecarlo.py`'s hash enters its
   key and because change 1 reaches the past targets it is fitted on.

The canonical run (seed 20261104, 5,000 draws) is compared with B, the site. It
differs from §1.333's GP arm in two ways, the ActionSA call and the re-emitted
width record, so it is not compared with GP.

## Predictions, against B

- **F1.** ActionSA's mean list share is 11.5–14.0%. It was 17.6%; its own
  centre was 12.64% on 21 October, with the by-election pull and the cap.
- **F2.** ActionSA's median seats are 24–33 (B 40).
- **F3.** The other five largest parties (DA, ANC, EFF, MK, PA) each gain list
  share, each by a factor of 1.03–1.09. The freed share goes to every party in
  proportion to its size, about (1 − 0.126) / (1 − 0.176) = 1.06.
- **F4.** P(DA largest alone) rises by at least 5 points and P(ANC largest
  alone) falls by at least 5. §1.330 measured the call moving both by more than
  10 points the other way. The ANC wins more wards than its list vote entitles
  it to, so the freed list vote converts into DA seats more than ANC seats.
- **F5.** The re-emitted width record differs from the current one only where a
  fold placeholder reached a past target. No party class's width changes by
  more than 5% of its value.
- **F6.** Of the ward favourites GP changed, wards 9 and 10 (to ALJAMAAH) and
  wards 17, 18, 68 and 82 (PA → DA) changed through γ alone. In the canonical
  run each stays changed unless ActionSA's lower level hands it to another
  party; any that differ are listed with the reason.
- **F7.** No party wins a majority alone in more than 1% of simulations.

## Checks before any result is read

- **K1.** `inputs_preflight.py --strict --city joburg --target 2026` is run and
  read (CLAUDE.md §4b). Its output is kept with the freeze.
- **K2.** The refit fold files with the status column equal the current files
  in every value column. Folds 3, 4 and 5 are refitted into scratch first: if
  θ or γ differs from disk, the vintage difference is reported before the
  re-emit, not absorbed into it.
- **K3.** The run's γ trace names a source for every party
  (`pooled 1+2` / `recent` / `default 1.0`). No placeholder is labelled as a
  fit.
- **K4.** `declares.py --verify` passes, and `test_intermediates_are_current`
  covers the pooled file and the fold files.

## What the owner receives

An old-vs-new report (B against the canonical run) in `reports/model-changes/`.
Then a UAT build. Going live needs the owner's yes.
