# What each candidate control actually moves

`run_model` called directly (never `montecarlo.py`, which overwrites the
city-year's artefacts), Johannesburg 2026, no `run_dir`, BLAS pinned to one
thread, 1,000 draws, seed 20261104 throughout — so every setting is drawn
against the same randomness and the difference is the lever, not the sample.

## Seat laws — read from the committed 5,000-draw regime artefacts, not re-run

| seat law | ANC | DA | ASA | EFF | PA | MK |
|---|---|---|---|---|---|---|
| deduct (ours) | 67 | 66 | 27 | 24 | 23 | 21 |
| expand — council grows | 67 | 68 | 28 | 25 | 24 | 22 |
| level — everyone topped up | 67 | 74 | 30 | 28 | 26 | 25 |
| cap — pure proportionality at 270 | **58** | 68 | 28 | 25 | 24 | 22 |

Per-party medians, which do not sum to the council.

## The scenario levers, median seats against a paired baseline

| setting | largest move |
|---|---|
| within-pool movement halved (`dirichlet_scale` 2.0) | 2 seats |
| within-pool movement doubled (`dirichlet_scale` 0.5) | 4 seats (ANC −4) |
| by-elections ignored (`w_bye` 0.0) | 4 seats (EFF +4) |
| by-elections trusted fully (`w_bye` 1.0) | 3 seats |
| per-VD turnout noise halved or doubled | **0** |
| ward-local by-elections switched on (0.75 / 0.35) | **0** |

## The two that read zero, re-measured on the MEAN

A median over 1,000 draws is an integer and cannot resolve an effect below
about half a seat, so "nothing moved" and "moved less than the instrument
reads" needed telling apart. Mean seats, same pairing:

| setting | largest move |
|---|---|
| `turnout_noise_sd` 0.04 (half) | **0.01 seats** |
| `turnout_noise_sd` 0.16 (double) | **0.01 seats** |
| `w_bye_local_ward` 0.75 + `w_bye_local_pr` 0.35 | **0.04 seats** |

⛔ Both are wired and reachable — `turnout_noise_sd` is consumed inside
`run_model` at `montecarlo.py:5092`, and `byelection_contest_detail.csv` is
present at this target. They are not undelivered. They simply do almost
nothing, across a four-fold range in one case and from off to the tested
values in the other.

**Neither can be a control.** A slider a reader moves through its whole range
for a hundredth of a seat is a control that lies about its own importance.

⚠️ `turnout_noise_sd` is per-VD noise — it is NOT the turnout LEVEL, nor a
per-pool differential. The turnout control the owner asked for ("low to high by
population group, and by area") does not exist in the model: it is
PUBLISHING-BACKLOG §9a decision 2, decided but unbuilt. This measurement says
nothing about it, and must not be read as saying turnout does not matter.

## What survives as a candidate control

The seat law, within-pool movement, and the citywide by-election weight.
