# Polling register — evidence for the δ/θ levers

Swept 2026-08-05. Anchors the polling lever endpoints; never fed in raw
(triangulate, do not anchor — plan §8.3). Update this file per wave.

| Pollster / wave | Fieldwork | Geography | n / method | Numbers |
|---|---|---|---|---|
| Ipsos Khayabus W2-2025 | Dec 25–Jan 26 | National LGE | 3,600 CAPI ±1.9% | ANC 38, DA 22, MK 13–14, EFF 12–13, ASA 4; 43–49% "politically homeless" |
| Ipsos same wave, metros | Q1 2026 | All-metro | subsample | ANC 35, DA 25, MK 14, EFF 13, ASA 4 (no 2026 Gauteng cut) |
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

## Integration path (agreed design, pending adoption decision)
1. `polling_lean` endpoints re-anchored to the current spread (Ipsos-style ↔
   SRF-Jul); default lean stays 0 until a second house corroborates.
2. CoJ-specific numbers may tilt θ modes via an explicit `w_poll` (clamped to
   §3.5 ranges, like `w_bye`) — NOT yet implemented; adoption changes
   published numbers and needs a decision + measured run.
3. Site: dated "figures as of" strip + changelog per re-run; new polls become
   interactive presets ("SRF July world").
