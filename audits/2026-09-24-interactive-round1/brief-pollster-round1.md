# Blind review brief — the interactive's model controls, and two findings

You are reviewing, as a senior election forecaster and survey methodologist,
design options for a public forecast of the Johannesburg council election of
4 November 2026 (270 seats: 135 wards first-past-the-post plus proportional
list seats; seats follow the COMBINED ward+list vote; a party that wins more
wards than its combined entitlement keeps them and takes no list seats — the
"excessive seats" clause).

Load the `pollster` skill first and review from that standpoint. You are
READ-ONLY: edit nothing, run nothing that writes. Do not sub-delegate.

The model: ~5,000 Monte Carlo simulations. Four voter "pools" = the four census
population groups (Black African, Coloured, Indian/Asian, White). Each pool's
party composition comes from an ecological fit to past ward results; an IPF
step binds the pool compositions to each party's citywide centre; a party-level
shock (Student-t) and a within-pool Dirichlet split are drawn per simulation;
turnout per pool is drawn from a triangular band; the citywide result is then
distributed over ~870 voting districts by a calibration that preserves each
district's historical deviation from the city (a parameter γ scales how much of
that local deviation is preserved). Seats are allocated by the statutory rule.

Code, for verification (read-only clone):
`/private/tmp/claude-501/-Users-simondavis-projects-jhb-election-model/2661b1d6-dd08-4a2f-a244-f9fff8f94798/scratchpad/repo`
— `src/montecarlo.py`, `src/pools.py`, `src/polling.py`, `src/scenarios.py`,
`JUDGEMENT-CALLS.md`, `MODEL-LOG.md`, `PUBLISHING-BACKLOG.md` §9–§10. Data is
on host `atlas` (`ssh atlas`, `~/projects/jhb-election-model`), read only.

The standard the project holds itself to: predictions are tested only against
real election results using data from before each election; agreement with an
earlier output of this model is evidence of nothing. A change that makes the
model more honest may ship even if a headline score worsens; one that scores
worse and explains nothing may not.

Provenance of the figures below. Re-derived independently by the lead: the turnout-by-pool table (A1), the poll screen (A3), every simulation count in A4 option (ii), both B1 tables, and B2 in full (two isolated trees, one of which reproduced the canonical 733 exactly). Taken from design agents' probes and NOT yet re-derived: the turnout-shift effects (A1), the mixing indices and probe effects (A2), the 2016 poll error figures (A3), the forcing results (A4 option i) and the override effects (A5). Check any you rely on.

---

## Part A — five reader controls for an interactive page

The page will run the real model in the reader's browser at ~300 simulations
per change, and let a reader move controls, overrule individual ward results,
and share the result as a link. For each item below: which option (if any) is
defensible to publish, what an expert critic would attack, and what is missing.

### A1. Turnout by community
Measured (joburg 2026, fixed seed, 150 draws, change in list-vote share pp /
mean seats), a logit shift δ to one pool's turnout band applied at three places:
* before the IPF: absorbed; residue small and NOT monotone in δ (Black African
  +0.5 → ANC −1.36pp; −0.5 → ANC +0.08pp).
* at the district level: absorbed by calibration (max change 1.4e-5 pp); only
  ward winners move (~0.8 seats per draw).
* after the IPF, in the pool turnout draw: moves shares monotonically —
  White +0.5: DA +2.74pp / +7.2 seats; White −0.5: DA −3.19 / −8.3;
  Black African +0.5: ANC +2.21 / +5.3, DA −3.50 / −8.6;
  Black African −0.5: ANC −2.73 / −6.8, DA +4.33 / +10.7.
  Citywide shares move; where in the city they move is spread by calibration,
  not concentrated in wards where the group lives.

Johannesburg turnout by pool, local elections (ecological, from ward totals):

| year | Black African | Coloured | Indian/Asian | White |
|---|---|---|---|---|
| 2000 | .352 | .330 | .160 | .529 |
| 2006 | .377 | .367 | .266 | .485 |
| 2011 | .508 | .601 | .458 | .643 |
| 2016 | .502 | .648 | .585 | .695 |
| 2021 | .364 | .543 | .408 | .527 |

2021 is the model's baseline. Candidate slider ranges, logits vs 2021:
(a) Johannesburg's own past levels — BA [−0.05, +0.59], Col [−0.88, +0.44],
Ind [−1.29, +0.71], Wh [−0.17, +0.72] (near one-sided for BA and White);
(b) the eight-metro panel's transition spread — ±0.62 / ±1.06 / ±1.06 / ±0.71
(94 transitions). The groups have mostly moved together: relative to the city,
BA −0.02..+0.14, Col −0.76..0, Ind −1.16..+0.13, White −0.08..+0.14.

The page would show "each party's support within each group". Two sources:
the 2021 ecological fit with Duncan–Davis bounds (informative for BA and White,
near-vacuous for Coloured and Indian/Asian — e.g. ANC among Coloured voters
12.6% [0.2–60.7]); or the 2026 matrix the simulation actually uses, which has
visible artefacts (PA 88.3% of the Coloured pool; MK 5.6% of the White pool).

### A2. "Do voters cross old lines?"
A public claim by one party (the DA) is that voters will increasingly vote
outside their community's historical pattern. A mixing index M (vote-weighted
distance of each unit's composition from the city's) measured on the record:
Johannesburg ward-level M 2000–2021: .327, .306, .313, .319, .326; pool-level
M: .385, .363, .391, .393, .361. Across eight metros 2006–2021, implied per-
cycle mixing λ = 1 − M_t/M_{t−1}: ward level 25 cycles, min −0.321 (a
boundary-change outlier), max +0.086, median −0.021 (15 of 25 negative, i.e.
polarising); pool level 19 cycles, min −0.158, max +0.081, median −0.006. The
DA's fitted share of the Black African pool in Johannesburg 2000→2021: .043,
.017, .039, .062, .020.

Mechanism fact: mixing pool compositions toward the city composition (weighted
by pool votes) leaves every party's citywide total unchanged by algebra, so in
this model "mixing" can only move geography (which wards a party wins), not
totals. Two implementations were probed at 300 draws: scaling γ (geography
only; citywide shares unchanged to 4 d.p.; within the recorded λ range the
effect is under 1 seat per party) and a literal pool-row blend (moved list
shares — e.g. EFF +3.7 seats at λ=+0.09 — for reasons not yet explained).

### A3. Reader-selected polls
Polls are OFF in the published forecast. Register screen at 2026 admits two
waves, both from one house (SRF/Victory Research: Feb–Mar 2026 DA 39 / ANC 30;
Jul 2026 DA 42 / ANC 18, n=504). Declined: a DA internal poll (commissioned,
no n), an Ipsos metro-aggregate, and older polls. A September 2026 Ipsos poll
with a Johannesburg cut (ANC 31 / DA 27–28 / ActionSA 14 / EFF 8 / MK 6) is
reported in the press and is NOT in the register. Scored history: three Ipsos
2016 metro polls (9 party readings: RMS error 3.02pp, MAE 2.55, max 5.52, all
nine implied swings the right sign) — one house, one cycle; SRF has no scored
local-election reading. A poll with no n is currently priced as MORE precise
than SRF (it falls back to a fixed σ). Proposed: reader may select polls;
point aggregate weighted by recency × sampling precision; a trust ceiling
w ≤ σm² / (σm² + E²) with E = 3.02pp (the measured RMS), so no reader setting
can give a poll more weight than the best-scored SA metro polls earned.
Measured effect, both SRF waves selected: ANC 27.4→24.2pp, DA 32.3→35.0pp;
July wave only: ANC 27.4→22.7.

### A4. A party's "best case" and "worst case"
The owner wants a reader to pick best or worst case for one or several
parties, limited by the fact that parties draw on shared voter pools.
Option (i) force inputs to favourable extremes (level shock at its 90th
percentile, favourable pools' turnout at the band's 90th percentile).
Measured: "DA best" lands near the DA's 97th percentile; "ActionSA best" near
its 69th (most of its spread is in the within-pool split, which has no
per-party extreme); DA+ActionSA both "best" gives DA 75 / ActionSA 31 — both
middling; ANC best + MK best reports an outcome 136 of 5,000 simulations reach
while their joint top-decile case occurs in 10 of 5,000.
Option (ii) select the model's own simulations where the party lands in its
top/bottom decile, intersecting for several parties. On the published 5,000:
DA best 544 (ties); DA+ActionSA best 30 (independence would give 55);
ANC worst + MK best 144 (52); ANC best + MK best 10 (57); ANC best + EFF best 5
(56). At 300 simulations per reader change, pairs keep 0–6 simulations, so
(ii) only works on the published run.

### A5. A reader's hand-made forecast
A reader may overrule any ward's winner. Seats still come from the statutory
allocation on each simulation's combined vote; an override changes seats only
where it triggers the excessive-seats clause or changes the count of wards won
by parties outside the list allocation. Measured (300 draws): flipping 10
ANC-modal wards to the DA: DA mean seats 67.6→69.0, ANC 64.1→60.2; all 71
ANC-modal wards: DA 111.8, ANC 46.6. The page would show, small and factual,
how far the reader's forecast is from ours, in whole seats, and a shared link
opens the friend's forecast recomputed on today's model.

---

## Part B — two findings about the published forecast

### B1. Small parties
Real council, 2021: 12 parties won seats; outside the seven largest, 6 parties
held 14 seats. Forecast, 2026: a median of 16 parties win seats per simulation
(90%: 12–19); outside the seven largest, a median of 30 seats (13–55). The
tail: seven small parties each win a seat in 60–98% of simulations; then about
40 micro-parties (many first-time) each win a seat in 6–7% of simulations —
together roughly 7 seats in a typical simulation. The 2026 ballot has 82
parties (75 with list candidates); in 2021 about 57. The 2026 specification
seeds 46 named new parties with no electoral history.

### B2. A change that made the model more honest and its seat error worse
A change made a new party with no measured history spread across the four
pools like the city's own composition, instead of exactly one quarter of its
support from each pool (which, for a small pool, can exceed what the pool can
cast). Backtest, 24 city-years, 1,000 draws, same seed: coherent seat error
723 → 733; CRPS 541.39 → 541.53. The 10 seats are five one-seat moves in party
medians (e.g. Ekurhuleni 2016 DA 81→80 vs actual 77; Cape Town 2021 GOOD 7→6
vs actual 9); one row improved.

---

## What to return (under ~1,500 words)
For each of A1–A5 and B1–B2: your verdict (defensible / defensible with
changes / not defensible), the specific attack an expert critic or journalist
would make, and what you would require before publication. Then your
priority order across all seven. State what you verified yourself in the code
or data and what you took from this brief.
