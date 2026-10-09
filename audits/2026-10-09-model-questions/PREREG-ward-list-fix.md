# Pre-registration: vote-weighted slate coverage in the ward/PR contestation change

Written 2026-10-09 before any model run of the change. Not edited after the
result; scored in `FINDINGS.md` in this directory.

## What was already run before this was written (diagnosis, not the fix)

- Live 2026 in-process runs at 1,000 draws, seed 20261104: baseline; contestation
  change neutralised (target slates = 2021 slates); the pre-2026-09-23 projection
  (`expand = 0.220`); `w_bye` 0 and 1.
- A world-only test with no model: 316 consecutive-LGE party pairs across eight
  metros, predicting each party's actual ward share at t from its actual list share
  at t times the t−1 ward/PR ratio times a slate change (none / count / vote-weighted).
  Count form MAE 0.427 pt, none 0.291 pt, vote-weighted 0.265 pt.
- Coverage values at Johannesburg 2026 from the certified slates and the 2021 file
  (`prereg_data.py`, no model run).

## The change

`montecarlo.run_model` multiplies each party's ward/PR ratio by `now / was`, where
both are the FRACTION OF WARDS the party fields a ward candidate in. Replace both
with the FRACTION OF THE PARTY'S OWN PREVIOUS-LGE LIST VOTE that lies in wards it
contests:

    coverage(p, year) = Σ_vd PR_prevLGE(p, vd) · 1[ward_year(vd) ∈ slate_year(p)]
                        / Σ_vd PR_prevLGE(p, vd)

over VDs present in `pools.vd_map(city, year)` (a split VD goes to the ward holding
most of its registered voters). `was` uses the previous LGE's slates and wards; `now`
uses the target's slates (result file at a backtest, `[roster.wards]` at 2026) and
the target's wards. Where a party had no list vote at the previous LGE the count
fraction is kept. The `[0, 2]` clip and every other line are unchanged. Tested as a
monkeypatch of `levels.contestation` (`votecov.py`); the repository is not edited.

Why: the measured ratio already reflects where the party stood; extending a slate
into wards where the party has no voters adds candidates, not votes. Counting wards
treats every ward as equally valuable to the party.

## Predictions (Johannesburg 2026, 1,000 draws, seed 20261104, against the baseline arm)

- **F1, PA ratio:** 2.000 → 1.029 (computed, no run).
- **F2, PA gap (list − ward), mean:** from −5.52 to within [−0.6, +0.2] points. Every
  draw's PA gap above −1.76 (the most negative non-independent gap in the 40 files);
  allowed to fail in at most 1% of draws.
- **F3, other parties' mean gaps** move by the removal of the ~6% normaliser
  inflation: DA +0.18 → [−1.8, −1.1]; ANC +0.80 → [−0.8, −0.3]; EFF −0.35 →
  [−1.2, −0.8]; ASA +3.27 → [+2.5, +3.0]; MK +1.00 → [+0.2, +0.6]. All five means
  inside the real envelope [−1.76, +6.16]. I expect the DA's per-draw gap to fall
  below −1.76 in more than 1% of draws (a separate defect: a ratio measured at 2021
  applied multiplicatively at other share levels), and that would not be a failure
  of this fix.
- **F4, PA seats and ward wins:** mean seats 23.95 → [16.0, 18.5]; mean ward wins
  10.4 → [4.5, 6.5].
- **F5, who gains:** DA and ANC mean seats each rise by 1.0–3.0; no other party
  moves by more than 1.5 seats except the PA.
- **F6, list shares:** the list-ballot (PR) share draws are bit-identical to the
  baseline arm (the ratio feeds only the ward target; the by-election conversion
  reads the ratio before the contestation change; the number of random numbers per
  draw does not depend on the ratio).

## Predictions (backtest panel, in-process, both arms identical seeds and draws)

Panel: the 24 city-years `compare_history.runnable` returns; 1,000 draws; scored
with `compare_history.run_city_year` in-process (no `history.json` written).

- **B1, list MAE (`pr_mae`):** identical at every city-year (same reasoning as F6).
- **B2, ward MAE (`ward_mae`, share-weighted, pp):** the panel mean falls. City-years
  where a party with a measurable list share at least doubled its ward count
  (Ekurhuleni 2021 PA, Nelson Mandela Bay 2021 PA, Johannesburg 2021 PA, Buffalo
  City 2016 AIC, Mangaung 2021 AIC) improve or hold; I expect no city-year to worsen
  by more than 0.15 pp.
- **B3, coherent seat error (`seat_abs_err_coherent`, summed over the panel):** falls
  (improves) by 0 to 15 seats. A rise of more than 4 seats falsifies it.
- **B4, ward winner accuracy:** no prediction of sign beyond "within draw noise";
  recorded only.

## What would make me withdraw the fix

B3 worse by more than 4 seats with B2 not improving; or F2 failing (the PA's gap still
outside the real envelope in more than 1% of draws).

## What this cannot claim

2026 has no result; F1–F6 are statements about the mechanism. Only B1–B4 are scored
against real elections, and contestation changes are large for few parties at any
backtest city-year, so B3 has little power.
