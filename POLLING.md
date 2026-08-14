# Polling register — evidence for the δ/θ levers

Swept 2026-08-05. Anchors the polling lever endpoints; never fed in raw
(triangulate, do not anchor — plan §8.3). Update this file per wave.

| Pollster / wave | Fieldwork | Geography | n / method | Numbers |
|---|---|---|---|---|
| Ipsos Khayabus W2-2025 | Dec 25–Jan 26 | National LGE | 3,600 CAPI ±1.9% | ANC 38, DA 22, MK 13–14, EFF 12–13, ASA 4; 43–49% "politically homeless" |
| Ipsos same wave, metros | Q1 2026 | All-metro | subsample | ANC 35, DA 25, MK 14, EFF 13, ASA 4, PA 4, IFP 2 (no 2026 Gauteng cut; PA/IFP from the same Ipsos release's minor-party table, carried in `polls.json` so the blend doesn't zero them) |
| SRF Q1-2026 national | 16 Feb–6 Mar | National LV (56% TO model) | 2,222 CATI | ANC 39, DA 28, MK 10, EFF 6, ASA 3 |
| SRF Q1-2026 **CoJ** | same | CoJ metro | ~503 | **DA 39, ANC 30, ASA 10, MK 8, EFF 4** |
| SRF Q1-2026 Gauteng | same | Gauteng | subsample | DA 37, ANC 31, ASA 7, EFF 5 (confirms prior anchor) |
| **SRF Q2-2026 CoJ** | **8–31 Jul, pub 5 Aug** | CoJ LV (53% TO model) | ~500 ±4.4% | **DA 42, ANC 18, MK 13, ASA 10, EFF 8** — ANC −12 vs Mar |
| DA internal (Zille, press) | rep. 1 Aug | CoJ | undisclosed | DA 40, ANC 27 |

Sources: thecommonsense.co.za (SRF releases incl. 2026-08-05 "ANC support
collapses Johannesburg"), ipsos.com press release 26 Mar 2026, News24 1 Aug
2026. No 2026 wave from Brenthurst, IRR, or any non-SRF house at CoJ/Gauteng
level. SRF Q2 national/Gauteng releases pending — re-check within days.

## Caveats (they carry the weight)
The two houses are structurally disjoint: Ipsos face-to-face registered-voter
with a huge unallocated undecided bloc vs SRF mobile-CATI likely-voter whose
turnout model screens out low-propensity (disproportionately ANC-leaning)
voters. CoJ reads rest on ~500-person subsamples. **SRF Jul ANC 18 is an
outlier below even the DA's own internal 27** — a −12pt move in four months is
single-house, single-wave evidence. SRF is DA-adjacent and publishes through
its own outlet. The honest lever input is the spread: CoJ DA-lead +9 (SRF
Mar) / +13 (DA internal) / +24 (SRF Jul). Both SRF waves hold ASA at 10 while
by-election evidence (W130 Soweto 22.7%) runs hotter. Pre-2021 precedent:
polls missed ActionSA by ~10pts in CoJ.

## The historical record, and what it says about NEW PARTIES (2026-08-14)

Searched because the model predicts one new party in thirty-two
(`src/arrivals.py`) and polls are the only pre-election evidence for a party
with no electoral history. Two findings, one of them decisive.

**There was exactly ONE independent pre-election poll for 2021**, and it had
ActionSA:

| pollster | fieldwork | n | ANC | DA | EFF | **ActionSA** | IFP | FF+ | ACDP |
|---|---|---|---|---|---|---|---|---|---|
| Ipsos (national) | 16–20 Aug 2021 | 1,501 | 49.3 | 17.9 | 14.5 | **1.5** | 1.4 | 1.2 | 1.5 |

ActionSA's actual national result was **2.34%**. The poll was low by a factor of
1.6 — against a model that is out by a factor of 3 in Johannesburg and 6 in
Tshwane. **The partisan poll was far worse**: ActionSA commissioned its own,
which reported the party "on course to win Joburg" against an eventual 16.05% and
third place. That is the case for admitting houses on track record and excluding
party-commissioned work, made concretely.

**The conversion from a national number to a metro one is the whole problem, and
it is arithmetic.** A party contesting few municipalities must be large in them:
if it takes X% of a territory but only stands in places holding share `s` of that
territory's vote, its average share where it stands is `X / s`. Both inputs are
public before polling day — the poll, and the nomination lists that say which
municipalities it contests.

Tested on every arrival in the eight-metro archive, as median |log ratio| between
estimate and actual metro share:

| | raw aggregate share | contested-area adjusted |
|---|---|---|
| 2016 (83 arrivals) | 1.609 | 0.000 |
| 2021 (175 arrivals) | 1.228 | **0.144** |

(2016 is trivially exact because almost every arrival stood in one metro; 2021 is
the real test.) For ActionSA the adjustment gives **9.78% wherever it stood**
against actuals of 18.12% (JHB), 9.28% (TSH), 7.36% (EKU) and 2.35% (ETH) — right
on average, and still needing the home-city effect to distribute between metros.

Feeding the POLL rather than the outcome, 1.5% national scales to about **6.3%
wherever ActionSA stood**. Against what the model actually produces:

| | Ipsos + conversion | model (honest) | actual |
|---|---|---|---|
| Johannesburg | 6.3% | 6.4% | 18.12% |
| Tshwane | 6.3% | 1.5% | 9.28% |
| Ekurhuleni | 6.3% | 1.5% | 7.36% |
| eThekwini | 6.3% | 1.5% | 2.35% |

Better in two metros, much better in one, worse in one. Nothing here would have
called Johannesburg — no available evidence did — but it closes most of the gap
in the metros where the model is currently silent.

**Sources:** Ipsos South Africa releases (ipsos.com/en-za); Wikipedia, *2021
South African municipal elections*, which is where the single national poll is
tabulated; thesouthafrican.com for the ActionSA-commissioned poll.

## Integration path (agreed design, pending adoption decision)
1. `polling_lean` endpoints re-anchored to the current spread (Ipsos-style ↔
   SRF-Jul); default lean stays 0 until a second house corroborates.
2. CoJ-specific numbers may tilt θ modes via an explicit `w_poll` (clamped to
   §3.5 ranges, like `w_bye`) — NOT yet implemented; adoption changes
   published numbers and needs a decision + measured run.
3. Site: dated "figures as of" strip + changelog per re-run; new polls become
   interactive presets ("SRF July world").
