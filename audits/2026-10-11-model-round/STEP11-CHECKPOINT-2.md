# Step 11, checkpoint 2: what moved, and the owner's wording (2026-10-16)

Branch `site-r11`. Old = what live version 836fd186 prints: the committed
`forecast-sheet.html`/`home.html` inline figures and the ledger's last
publication (2026-10-11, run `r-c68c627d287e-e6f5c4f1-dirty`). New = the
16 October run (`r-62a94ccdfef2`, seat draws `6e06c99a…`), measured by a
scratch render (`render_sheet.main --sheet <scratch>` with `claims_faults` and
the Zille box's `[[wall_anc_span]]` bypassed in memory; the tree was not
written) and a dry `build_site.py --out <scratch> --ledger-root <copy>`.

## Blocked until the owner edits `content/joburg/claims.toml`

`render_sheet.py` refuses on the new run, so `/forecast`, `/claims`, the
articles and the claim pages cannot be regenerated:

1. **The DA cannot win Joburg without Soweto**: verdict VERY LIKELY, chance
   the claim holds 0.7134, which the scale calls QUITE LIKELY. The claim's
   `requires_at_least = "QUITE LIKELY"` already licenses its text at the lower
   verdict, and step 4 ("All told, Mashaba is … correct") is generated from it.
2. **490,000 DA voters would win the DA an outright majority**: the `since`
   box names `[[wall_count]]`, `[[wall_flips]]` and `[[wall_anc_span]]`. The DA
   now wins alone in no simulation, so there is no wall range to print.

Resume, once both are edited:

    .venv/bin/python src/render_sheet.py
    .venv/bin/python src/render_home.py
    cp -R publications <scratch>/ledger        # the UAT copy
    .venv/bin/python audits/2026-10-11-model-round/step11_retire.py --root <scratch>/ledger
    .venv/bin/python src/build_site.py --ledger-root <scratch>/ledger --publish \
        --change-class mechanism --reason "Forecast updated 16 October 2026: the IEC's September roll, each voting district counted in one ward, parties placed from their own national results, ward-only candidates limited to their wards."
    git status --short --ignored site/          # then commit site/
    env -u CLOUDFLARE_API_TOKEN npx wrangler versions upload --message "$(git log -1 --format='%h %s')"

Live promotion repeats `step11_retire.py` without `--root` (the real ledger).

## Claims (the owner's text; drafts only)

Chance = the chance the claim holds, as `claims.toml`'s `chance` names it.

| claim (published) | figure | old | new | verdict old → scale now |
|---|---|---|---|---|
| The DA cannot win Joburg without Soweto (7 Oct) | chance it holds (1 − DA governs without a Soweto ward) | 0.7650 | 0.7134 | VERY LIKELY → QUITE LIKELY |
| | Soweto wards (`areas.toml`; ward 29 crossed the 0.5 cut on the 2026 roll) | 40 | 41 | |
| | DA wins no Soweto ward | 97.3% | 99.94% | |
| | DA governs with no Soweto ward | 23.5% | 28.7% | |
| | … with ActionSA and the PA / with the ANC | 12.4% / 15.8% | 5.1% / 27.3% | |
| | DA wins a Soweto ward / then governs | 2.7% / 88.2% | 0.06% (3 simulations) / 66.7% | |
| | DA leading the parties outside the ANC, EFF, MK | 82.6% | 77.8% | |
| A majority without the ANC, the EFF and MK is possible for the DA (26 Sep) | chance it holds | 0.8712 | 0.7848 | VERY LIKELY → VERY LIKELY |
| | DA + ANC clear 136 | 42.7% | 68.1% | |
| | DA + ActionSA + PA clear 136; median; median when they do | 16.2%; 117; 143 | 5.3%; 114; 139 | |
| | ANC-led, without DA, EFF, MK | 78.1% | 75.4% | |
| MK will be the biggest party in the city (26 Sep) | chance it holds | 0.0144 | 0.0564 | EXTREMELY UNLIKELY → EXTREMELY UNLIKELY |
| | MK median; top of range (95th pct) | 22; 50 | 17; 64 | |
| | ANC / DA median seats | 66 / 66 | 74 / 70 | |
| | ANC alone largest / DA alone / tie | 46.7% / 45.2% / 1.4% | 54.1% / 35.9% / 3.7% | |
| The ANC can govern Johannesburg alone again (26 Sep) | chance it holds | 0.0002 (1 simulation) | 0 (none) | NEAR IMPOSSIBLE → NEAR IMPOSSIBLE |
| | ANC best result; median | 144; 66 | 103; 74 | |
| | ANC + EFF + MK clear 136; median | 11.6%; 116 | 19.7%; 124 | |
| 490,000 DA voters would win the DA an outright majority (7 Aug) | DA alone (no surge) | 0.06% (3) | 0 (none) | FALSE (not chance-rated) |
| | of those, 30+ ANC wards taken | 3 | 0 | |

Draft "Since then" notes (dated 16 October 2026; every figure a token at
render):

- **Soweto.** "Since then the forecast reads the IEC's September roll, which
  puts ward 29 in Soweto: 41 wards. The DA wins none of them in 99.9% of
  simulations. Without one it governs in 29%: with ActionSA and the PA in 5%,
  with the ANC in 27%. The claim holds with a 71% chance, which the scale calls
  quite likely." Step 3 now rests on 3 simulations.
- **Red lines.** "Since then the rest of the council, without the ANC, the EFF
  and MK, clears 136 in 78% of simulations. The DA and the ANC together clear
  it in 68%; the DA with ActionSA and the PA in 5%."
- **MK.** "Since then MK is the largest party in 6% of simulations. Its median
  is 17 seats and the top of its range 64, against the ANC's 74 and the DA's
  70."
- **ANC alone.** The current box would read "0.0% chance (0 of the 5,000
  simulations) … When this claim was first written it did so in none of
  them." Draft: "Since then the ANC reaches a majority on its own in none of
  the 5,000 simulations. Its best result is 103 seats."
- **490,000.** Draft box: "The turnout setting this test used is no longer in
  the model, so the surge cannot be re-run. In today's forecast, with no
  surge, the DA wins a majority on its own in none of the 5,000 simulations.
  **The verdict stands.**"

## Articles and live pages

| page | figure | old | new | wording |
|---|---|---|---|---|
| Nobody will win Johannesburg (8 Aug), "what the model says now" | ANC alone largest / DA alone / tie | 47% / 45% / 1.4% | 54% / 36% / 3.7% | "The largest party is a near tie, where on 8 August the DA led clearly" no longer fits. Draft: "The ANC is now ahead for largest party, where on 8 August the DA led clearly: …" |
| | one party alone | 0.1% | 0.2% | holds |
| | ANC excessive seats; wards; entitlement | 62%; 60; 58 | 81%; 69; 65 | "weaker than published" (published 96%, 74 on 65) holds |
| Laingsburg, 2021 (8 Aug), since box | ANC wards; entitlement; excessive | 60; 58; 62% | 69; 65; 81% | holds |
| Home lede (live, generated) | "The largest party is …" | too close to call | leaning to the ANC | generated by `render_home.phrases` |
| | ANC / DA largest; one party alone | 47% / 45%; 0.08% | 54% / 36%; 0.18% | |
| | seat middles ANC, DA, EFF, ASA, MK, PA | 66, 66, 25, 27, 22, 23 | 74, 70, 29, 27, 17, 14 | |
| /forecast | ANC + DA majority | 43% | 68% | |
| /methodology | small-party surge share; ANC excessive | 9.0%; 62% | 0.9%; 81% | |
| /your-forecast | by-election "fully" moves, roll, turnout, MK/RISE group votes | see `site/changes.json` | | |

## Live text that may have been wrong when published (owner: correction or not)

- /methodology, live since 26 September: ActionSA "{{hist_asa_npe_2024}}
  nationally in 2024". The figure (6.22%) is ActionSA's share of
  Johannesburg's 2024 national ballot, not its national share.
- /methodology step 1, live: "registered in each of Johannesburg's voting
  districts … not estimated, projected or adjusted". The live forecast split
  181 voting districts between wards by the Demarcation Board's part figures.
- /methodology step 2, live: "the model carries one extra pool … the IFP".
  Whether the live run's `pools_2026.json` carried it is not checked here.

## Owner decisions applied (2026-10-16) and the UAT version

Soweto verdict QUITE LIKELY with its since box; the 490,000 box is the
owner's text; two corrections on /corrections; the other since drafts are on
UAT for review. UAT version `d22294e0-28de-4580-99d6-b0aad362076b`,
https://d22294e0-joburg-whysoserious.psi-02e.workers.dev, commit `d482584`.
`step11_retire.py` retires 35 tokens (the regenerated sheet dropped 24 more:
two claim boxes' figures, two coalitions below the table's 5% cut, two
excessive-seat tile names).

Still open before live: the real-ledger retirements; a draws re-export after
the live `--publish` (`test_served_draws`: the cells name the old run);
`test_reweight`'s paired re-run (the shifted run moves no seat, so the
re-weighting cannot be checked against it on this model).
